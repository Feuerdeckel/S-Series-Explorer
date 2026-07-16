"""Tests for S-Series Explorer helper functions."""

from pathlib import Path

from s_series_explorer import SSeriesExplorer

__version__ = "1.1.0"


def test_format_size() -> None:
    assert SSeriesExplorer._format_size(0) == "0 B"
    assert SSeriesExplorer._format_size(1023) == "1023 B"
    assert SSeriesExplorer._format_size(1024) == "1.0 KB"
    assert SSeriesExplorer._format_size(1024 * 1024) == "1.0 MB"


def test_unique_target(tmp_path: Path) -> None:
    original = tmp_path / "demo.txt"
    original.write_text("demo", encoding="utf-8")
    copy_1 = tmp_path / "demo - Kopie 1.txt"
    copy_1.write_text("demo", encoding="utf-8")

    assert SSeriesExplorer._unique_target(original) == tmp_path / "demo - Kopie 2.txt"


def test_icon_key_for_path() -> None:
    assert SSeriesExplorer._icon_key_for_path(Path("demo"), is_dir=True) == "folder"
    assert SSeriesExplorer._icon_key_for_path(Path("notes.txt")) == "text"
    assert SSeriesExplorer._icon_key_for_path(Path("photo.png")) == "image"
    assert SSeriesExplorer._icon_key_for_path(Path("script.py")) == "code"
    assert SSeriesExplorer._icon_key_for_path(Path("backup.zip")) == "archive"
    assert SSeriesExplorer._icon_key_for_path(Path("manual.pdf")) == "pdf"
    assert SSeriesExplorer._icon_key_for_path(Path("unknown.bin")) == "file"
