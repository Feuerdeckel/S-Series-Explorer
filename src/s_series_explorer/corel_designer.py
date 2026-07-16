from __future__ import annotations

import re
import zipfile
from pathlib import Path

from .models import CorelDesignerInfo

_MAX_DIRECT_READ = 8 * 1024 * 1024
_MAX_ZIP_MEMBER_READ = 3 * 1024 * 1024

_MARKER_RE = re.compile(rb"CDR([0-9A-Z])(?:vrsn|fver|fver|vers|ver)", re.IGNORECASE)
_PRODUCT_RE = re.compile(
    rb"Corel(?:DRAW|\s+DESIGNER|DRAW\s+Technical\s+Suite)[^\x00\r\n]{0,80}",
    re.IGNORECASE,
)
_VERSION_RE = re.compile(rb"(?:version|v)\s*([0-9]{1,2}(?:\.[0-9]+)?|X[4-8])", re.IGNORECASE)

_MAJOR_HINTS = {
    10: "Corel DESIGNER 10",
    12: "Corel DESIGNER 12",
    14: "Corel DESIGNER X4",
    15: "Corel DESIGNER X5",
    16: "Corel DESIGNER X6",
    17: "Corel DESIGNER X7",
    19: "CorelDRAW Technical Suite 2017",
    20: "CorelDRAW Technical Suite 2018",
    21: "CorelDRAW Technical Suite 2019",
    22: "CorelDRAW Technical Suite 2020",
    23: "CorelDRAW Technical Suite 2021",
    24: "CorelDRAW Technical Suite 2022/2023",
    25: "CorelDRAW Technical Suite 2024",
    26: "CorelDRAW Technical Suite 2025",
}


def inspect_corel_designer(path: Path) -> CorelDesignerInfo:
    if path.suffix.casefold() != ".des":
        return CorelDesignerInfo()

    try:
        with path.open("rb") as stream:
            head = stream.read(16)
    except OSError as exc:
        return CorelDesignerInfo(
            display="Lesefehler",
            confidence="none",
            notes=[str(exc)],
        )

    buffers: list[tuple[str, bytes]] = []
    container_hint = "Binär"

    if head.startswith(b"PK"):
        container_hint = "ZIP-Container"
        try:
            with zipfile.ZipFile(path) as archive:
                preferred = sorted(
                    archive.namelist(),
                    key=lambda name: (
                        0
                        if any(
                            marker in name.casefold()
                            for marker in ("riffdata", "root.dat", "metadata", "version")
                        )
                        else 1,
                        name.casefold(),
                    ),
                )
                for name in preferred[:30]:
                    info = archive.getinfo(name)
                    if info.is_dir() or info.file_size > _MAX_ZIP_MEMBER_READ:
                        continue
                    try:
                        buffers.append((name, archive.read(name)))
                    except (OSError, RuntimeError, zipfile.BadZipFile):
                        continue
        except (OSError, zipfile.BadZipFile) as exc:
            return CorelDesignerInfo(
                display="DES (ZIP beschädigt)",
                confidence="low",
                notes=[str(exc)],
            )
    else:
        if head.startswith(b"RIFF"):
            container_hint = "RIFF"
        try:
            with path.open("rb") as stream:
                buffers.append((path.name, stream.read(_MAX_DIRECT_READ)))
        except OSError as exc:
            return CorelDesignerInfo(
                display="Lesefehler",
                confidence="none",
                notes=[str(exc)],
            )

    marker = _find_marker(buffers)
    product_text = _find_product_text(buffers)

    if marker:
        code, source = marker
        major = _decode_major(code)
        hint = _MAJOR_HINTS.get(major, f"Corel-Formatversion {major}" if major else "")
        display = hint or f"Corel-Formatcode {code}"
        notes = [f"Container: {container_hint}", f"Marker in: {source}"]
        if product_text:
            notes.append(f"Produkttext: {product_text}")
        return CorelDesignerInfo(
            display=display,
            format_code=code,
            format_major=major,
            product_hint=product_text or hint,
            confidence="high",
            notes=notes,
        )

    if product_text:
        version = _extract_version(product_text.encode("latin-1", errors="ignore"))
        display = f"{product_text}{f' ({version})' if version else ''}"
        return CorelDesignerInfo(
            display=display,
            product_hint=product_text,
            confidence="medium",
            notes=[f"Container: {container_hint}", "Kein CDR-Versionsmarker gefunden"],
        )

    return CorelDesignerInfo(
        display="DES – Version nicht erkannt",
        confidence="low",
        notes=[
            f"Container: {container_hint}",
            "Die Datei kann aus einer nicht unterstützten oder älteren DES-Generation stammen.",
        ],
    )


def _find_marker(buffers: list[tuple[str, bytes]]) -> tuple[str, str] | None:
    for source, data in buffers:
        match = _MARKER_RE.search(data)
        if match:
            return match.group(1).decode("ascii", errors="replace").upper(), source
    return None


def _find_product_text(buffers: list[tuple[str, bytes]]) -> str:
    for _, data in buffers:
        match = _PRODUCT_RE.search(data)
        if match:
            raw = match.group(0).replace(b"\x00", b" ")
            return " ".join(raw.decode("latin-1", errors="ignore").split())[:120]
    return ""


def _extract_version(data: bytes) -> str:
    match = _VERSION_RE.search(data)
    return match.group(1).decode("ascii", errors="ignore") if match else ""


def _decode_major(code: str) -> int | None:
    if len(code) != 1:
        return None
    if code.isdigit():
        return int(code)
    if "A" <= code <= "Z":
        return 10 + ord(code) - ord("A")
    return None
