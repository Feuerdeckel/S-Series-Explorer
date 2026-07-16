from __future__ import annotations

import csv
from pathlib import Path

from .models import ComparisonRow


def export_rows(path: Path, rows: list[ComparisonRow]) -> None:
    data = [row.as_dict() for row in rows]
    if not data:
        raise ValueError("Keine Daten zum Exportieren")
    with path.open("w", newline="", encoding="utf-8-sig") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(data[0]))
        writer.writeheader()
        writer.writerows(data)
