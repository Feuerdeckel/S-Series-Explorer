import tempfile
import unittest
import zipfile
from pathlib import Path

from s_series_explorer.corel_designer import inspect_corel_designer


class CorelDesignerTests(unittest.TestCase):
    def test_detects_riff_marker(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "example.des"
            path.write_bytes(b"RIFF" + b"\x00" * 12 + b"CDRFvrsn")
            result = inspect_corel_designer(path)
            self.assertEqual(result.format_major, 15)
            self.assertEqual(result.confidence, "high")

    def test_detects_marker_inside_zip(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "example.des"
            with zipfile.ZipFile(path, "w") as archive:
                archive.writestr("content/riffData.cdr", b"CDRGfver")
            result = inspect_corel_designer(path)
            self.assertEqual(result.format_major, 16)
            self.assertEqual(result.confidence, "high")


if __name__ == "__main__":
    unittest.main()
