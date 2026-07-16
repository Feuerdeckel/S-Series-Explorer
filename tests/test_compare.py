import tempfile
import unittest
from pathlib import Path

from s_series_explorer.compare import MODE_RELATIVE_PATH, compare_records
from s_series_explorer.scanner import scan_folder


class CompareTests(unittest.TestCase):
    def test_detects_same_changed_and_missing(self) -> None:
        with tempfile.TemporaryDirectory() as a_name, tempfile.TemporaryDirectory() as b_name:
            a = Path(a_name)
            b = Path(b_name)
            (a / "same.xml").write_text("same", encoding="utf-8")
            (b / "same.xml").write_text("same", encoding="utf-8")
            (a / "changed.xml").write_text("left", encoding="utf-8")
            (b / "changed.xml").write_text("right", encoding="utf-8")
            (a / "only-a.xml").write_text("a", encoding="utf-8")
            (b / "only-b.xml").write_text("b", encoding="utf-8")

            rows = compare_records(
                scan_folder(a),
                scan_folder(b),
                mode=MODE_RELATIVE_PATH,
            )
            statuses = {row.record.filename: row.status for row in rows}
            self.assertEqual(statuses["same.xml"], "Identisch")
            self.assertEqual(statuses["changed.xml"], "Geändert")
            self.assertEqual(statuses["only-a.xml"], "Nur Ordner A")
            self.assertEqual(statuses["only-b.xml"], "Nur Ordner B")


if __name__ == "__main__":
    unittest.main()
