from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

__version__ = "0.2.0"


@dataclass(slots=True)
class ParsedFilename:
    original_name: str
    stem: str
    extension: str
    object_type: str
    code_segments: list[str] = field(default_factory=list)
    issue: str = ""
    in_work: str = ""
    language: str = ""
    country: str = ""
    semantic_fields: dict[str, str] = field(default_factory=dict)
    is_valid: bool = True
    messages: list[str] = field(default_factory=list)

    def segment(self, index: int) -> str:
        return self.code_segments[index] if index < len(self.code_segments) else ""


@dataclass(slots=True)
class CorelDesignerInfo:
    display: str = ""
    format_code: str = ""
    format_major: int | None = None
    product_hint: str = ""
    confidence: str = "none"
    notes: list[str] = field(default_factory=list)


@dataclass(slots=True)
class FileRecord:
    root: Path
    path: Path
    relative_path: str
    filename: str
    parsed: ParsedFilename
    size: int
    modified_timestamp: float
    modified_display: str
    corel: CorelDesignerInfo = field(default_factory=CorelDesignerInfo)
    sha256: str = ""

    @property
    def normalized_stem(self) -> str:
        return self.parsed.stem.casefold()

    @property
    def normalized_relative_path(self) -> str:
        return self.relative_path.replace("\\", "/").casefold()


@dataclass(slots=True)
class ComparisonRow:
    status: str
    left: FileRecord | None = None
    right: FileRecord | None = None
    details: str = ""

    @property
    def record(self) -> FileRecord:
        if self.left is not None:
            return self.left
        if self.right is not None:
            return self.right
        raise RuntimeError("ComparisonRow contains no file record")

    def as_dict(self) -> dict[str, Any]:
        record = self.record
        parsed = record.parsed
        return {
            "status": self.status,
            "object_type": parsed.object_type,
            **{f"segment_{i + 1}": parsed.segment(i) for i in range(12)},
            "issue": parsed.issue,
            "in_work": parsed.in_work,
            "language": parsed.language,
            "country": parsed.country,
            "corel_version": record.corel.display,
            "extension": parsed.extension,
            "size": record.size,
            "modified": record.modified_display,
            "relative_path": record.relative_path,
            "filename": record.filename,
            "valid": parsed.is_valid,
            "messages": "; ".join(parsed.messages),
            "comparison_details": self.details,
            "left_path": str(self.left.path) if self.left else "",
            "right_path": str(self.right.path) if self.right else "",
        }
