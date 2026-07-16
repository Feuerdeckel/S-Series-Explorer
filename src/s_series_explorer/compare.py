from __future__ import annotations

from collections import defaultdict
from collections.abc import Callable

from .models import ComparisonRow, FileRecord
from .scanner import ensure_hashes

MODE_RELATIVE_PATH = "Relativer Pfad"
MODE_FILENAME = "Dateiname ohne Endung"
MODE_CONTENT = "Dateiinhalt (SHA-256)"
COMPARISON_MODES = (MODE_RELATIVE_PATH, MODE_FILENAME, MODE_CONTENT)


def compare_records(
    left: list[FileRecord],
    right: list[FileRecord],
    *,
    mode: str,
    progress: Callable[[int, str], None] | None = None,
) -> list[ComparisonRow]:
    if mode == MODE_CONTENT:
        ensure_hashes(left, progress)
        ensure_hashes(right, progress)
        return _compare_by_key(left, right, key=lambda item: item.sha256, content_mode=True)
    if mode == MODE_FILENAME:
        return _compare_by_key(left, right, key=lambda item: item.normalized_stem)
    return _compare_by_key(left, right, key=lambda item: item.normalized_relative_path)


def _compare_by_key(
    left: list[FileRecord],
    right: list[FileRecord],
    *,
    key: Callable[[FileRecord], str],
    content_mode: bool = False,
) -> list[ComparisonRow]:
    left_map: dict[str, list[FileRecord]] = defaultdict(list)
    right_map: dict[str, list[FileRecord]] = defaultdict(list)
    for item in left:
        left_map[key(item)].append(item)
    for item in right:
        right_map[key(item)].append(item)

    rows: list[ComparisonRow] = []
    for match_key in sorted(set(left_map) | set(right_map)):
        left_items = left_map.get(match_key, [])
        right_items = right_map.get(match_key, [])
        pair_count = min(len(left_items), len(right_items))

        for index in range(pair_count):
            left_item = left_items[index]
            right_item = right_items[index]
            if content_mode:
                status = "Gleicher Inhalt"
                details = "SHA-256 identisch"
            else:
                same_content = _same_content_fast(left_item, right_item)
                status = "Identisch" if same_content else "Geändert"
                details = (
                    "Größe und Inhalt identisch"
                    if same_content
                    else _difference_text(left_item, right_item)
                )
            if len(left_items) > 1 or len(right_items) > 1:
                details = f"Mehrfachtreffer; {details}"
            rows.append(ComparisonRow(status=status, left=left_item, right=right_item, details=details))

        for item in left_items[pair_count:]:
            rows.append(
                ComparisonRow(
                    status="Nur Ordner A",
                    left=item,
                    details="Kein passender Eintrag in Ordner B",
                )
            )
        for item in right_items[pair_count:]:
            rows.append(
                ComparisonRow(
                    status="Nur Ordner B",
                    right=item,
                    details="Kein passender Eintrag in Ordner A",
                )
            )

    rows.sort(key=lambda row: (row.status, row.record.relative_path.casefold()))
    return rows


def _same_content_fast(left: FileRecord, right: FileRecord) -> bool:
    if left.size != right.size:
        return False
    if left.sha256 and right.sha256:
        return left.sha256 == right.sha256
    # "Inhalt vergleichen" must be exact. Equal size and timestamp are not
    # sufficient, so paired files are compared byte for byte in chunks.
    return _files_equal(left, right)


def _files_equal(left: FileRecord, right: FileRecord, chunk_size: int = 1024 * 1024) -> bool:
    try:
        with left.path.open("rb") as a, right.path.open("rb") as b:
            while True:
                a_chunk = a.read(chunk_size)
                b_chunk = b.read(chunk_size)
                if a_chunk != b_chunk:
                    return False
                if not a_chunk:
                    return True
    except OSError:
        return False


def _difference_text(left: FileRecord, right: FileRecord) -> str:
    differences: list[str] = []
    if left.size != right.size:
        differences.append(f"Größe {left.size} ↔ {right.size} Bytes")
    if int(left.modified_timestamp) != int(right.modified_timestamp):
        differences.append("Änderungszeit unterschiedlich")
    if not differences:
        differences.append("Dateiinhalt unterschiedlich")
    return ", ".join(differences)
