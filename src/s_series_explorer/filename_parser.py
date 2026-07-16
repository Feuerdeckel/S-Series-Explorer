from __future__ import annotations

import re
from pathlib import Path

from .models import ParsedFilename

_ALLOWED_CODE = re.compile(r"^[A-Z0-9]+$")
_KNOWN_PREFIXES = {
    "DMC",
    "PMC",
    "ICN",
    "COM",
    "DDN",
    "DML",
    "CSN",
    "SMC",
    "BREX",
    "ACT",
    "CCT",
    "PCT",
}


def parse_filename(filename: str) -> ParsedFilename:
    path = Path(filename)
    extension = path.suffix.lower().lstrip(".")
    stem = path.stem
    result = ParsedFilename(
        original_name=filename,
        stem=stem,
        extension=extension,
        object_type="DATEI",
    )

    if not stem:
        result.is_valid = False
        result.messages.append("Leerer Dateiname")
        return result

    if stem != stem.upper():
        result.messages.append("Dateiname enthält Kleinbuchstaben")

    if " " in stem:
        result.is_valid = False
        result.messages.append("Dateiname enthält Leerzeichen")

    parts = stem.split("_")
    code_part = parts[0]
    suffix_parts = parts[1:]

    code_tokens = code_part.split("-")
    prefix = code_tokens[0].upper() if code_tokens else ""
    result.object_type = prefix if prefix in _KNOWN_PREFIXES else "DATEI"
    result.code_segments = code_tokens[1:] if prefix in _KNOWN_PREFIXES else code_tokens

    if any(token == "" for token in code_tokens):
        result.is_valid = False
        result.messages.append("Leeres Segment zwischen Bindestrichen")

    for token in code_tokens:
        if token and not _ALLOWED_CODE.fullmatch(token.upper()):
            result.is_valid = False
            result.messages.append(f"Ungültige Zeichen im Segment '{token}'")

    _parse_suffixes(result, suffix_parts)
    _apply_semantics(result)
    _validate_known_type(result)
    return result


def _parse_suffixes(result: ParsedFilename, suffix_parts: list[str]) -> None:
    for part in suffix_parts:
        tokens = part.split("-")
        if len(tokens) == 2 and tokens[0].isdigit() and tokens[1].isdigit() and not result.issue:
            result.issue, result.in_work = tokens
            continue
        if (
            len(tokens) == 2
            and len(tokens[0]) in (2, 3)
            and len(tokens[1]) == 2
            and tokens[0].isalpha()
            and tokens[1].isalpha()
            and not result.language
        ):
            result.language, result.country = (token.upper() for token in tokens)
            continue
        result.messages.append(f"Nicht zugeordnetes Suffix '{part}'")


def _apply_semantics(result: ParsedFilename) -> None:
    seg = result.code_segments
    if result.object_type == "DMC":
        labels = [
            "modelIdentCode",
            "systemDiffCode",
            "systemCode",
            "subSystemAndSubSubSystemCode",
            "assyCode",
            "disassyCodeAndVariant",
            "infoCodeAndVariant",
            "itemLocationCode",
            "learnCodeOrExtension",
        ]
        result.semantic_fields.update(
            {label: value for label, value in zip(labels, seg, strict=False)}
        )
        if len(seg) >= 4:
            result.semantic_fields["subSystemCode"] = seg[3][:1]
            result.semantic_fields["subSubSystemCode"] = seg[3][1:2]
        if len(seg) >= 6:
            result.semantic_fields["disassyCode"] = seg[5][:2]
            result.semantic_fields["disassyCodeVariant"] = seg[5][2:]
        if len(seg) >= 7:
            result.semantic_fields["infoCode"] = seg[6][:3]
            result.semantic_fields["infoCodeVariant"] = seg[6][3:]
    elif result.object_type == "PMC":
        labels = [
            "modelIdentCode",
            "pmIssuer",
            "pmNumber",
            "pmVolume",
            "extension1",
            "extension2",
        ]
        result.semantic_fields.update(
            {label: value for label, value in zip(labels, seg, strict=False)}
        )
    elif result.object_type == "ICN":
        labels = [
            "modelOrProjectCode",
            "originatorOrSecurityCode",
            "graphicCode",
            "variant",
            "sequenceOrDrawingCode",
            "sheetOrSecondaryCode",
            "extension1",
            "issue",
            "inWorkOrSheet",
        ]
        result.semantic_fields.update(
            {label: value for label, value in zip(labels, seg, strict=False)}
        )
    else:
        result.semantic_fields.update(
            {f"segment{i + 1}": value for i, value in enumerate(seg)}
        )


def _validate_known_type(result: ParsedFilename) -> None:
    count = len(result.code_segments)
    if result.object_type == "DMC" and count < 8:
        result.is_valid = False
        result.messages.append("DMC hat weniger als 8 Code-Segmente")
    elif result.object_type == "PMC" and count < 4:
        result.is_valid = False
        result.messages.append("PMC hat weniger als 4 Code-Segmente")
    elif result.object_type == "ICN" and count < 3:
        result.is_valid = False
        result.messages.append("ICN hat weniger als 3 Code-Segmente")

    if result.object_type in _KNOWN_PREFIXES and result.original_name[:3] != result.object_type[:3]:
        result.messages.append("Präfix-Schreibweise wurde normalisiert")

    if result.issue and len(result.issue) not in (2, 3):
        result.messages.append("Ungewöhnliche Ausgabenummer")
    if result.in_work and len(result.in_work) != 2:
        result.messages.append("Ungewöhnlicher In-Work-Stand")
