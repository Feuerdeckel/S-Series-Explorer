from __future__ import annotations

import hashlib
from datetime import datetime
from pathlib import Path
from typing import Callable, Iterable

from .corel_designer import inspect_corel_designer
from .filename_parser import parse_filename
from .models import CorelDesignerInfo, FileRecord

__version__ = "0.2.0"

ProgressCallback = Callable[[int, str], None]


def scan_folder(
    root: Path,
    *,
    recursive: bool = True,
    calculate_hashes: bool = False,
    include_directories: bool = False,
    progress: ProgressCallback | None = None,
) -> list[FileRecord]:
    root = root.expanduser().resolve()
    if not root.is_dir():
        raise NotADirectoryError(str(root))

    paths = list(_iter_entries(root, recursive=recursive, include_directories=include_directories))
    records: list[FileRecord] = []
    total = len(paths)

    for index, path in enumerate(paths, start=1):
        try:
            stat = path.stat()
        except OSError:
            continue

        parsed = parse_filename(path.name)
        corel = CorelDesignerInfo() if path.is_dir() else inspect_corel_designer(path)
        digest = sha256_file(path) if calculate_hashes and path.is_file() else ""
        record = FileRecord(
            root=root,
            path=path,
            relative_path=str(path.relative_to(root)),
            filename=path.name,
            parsed=parsed,
            size=stat.st_size,
            modified_timestamp=stat.st_mtime,
            modified_display=datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M"),
            corel=corel,
            sha256=digest,
        )
        records.append(record)
        if progress:
            progress(index * 100 // max(total, 1), path.name)

    records.sort(key=lambda item: item.relative_path.casefold())
    return records


def ensure_hashes(records: list[FileRecord], progress: ProgressCallback | None = None) -> None:
    missing = [record for record in records if not record.sha256]
    for index, record in enumerate(missing, start=1):
        record.sha256 = sha256_file(record.path)
        if progress:
            progress(index * 100 // max(len(missing), 1), record.filename)


def sha256_file(path: Path, chunk_size: int = 1024 * 1024) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        while chunk := stream.read(chunk_size):
            digest.update(chunk)
    return digest.hexdigest()


def _iter_entries(root: Path, *, recursive: bool, include_directories: bool) -> Iterable[Path]:
    iterator = root.rglob("*") if recursive else root.glob("*")
    for path in iterator:
        if path.is_file() or (include_directories and path.is_dir()):
            yield path
