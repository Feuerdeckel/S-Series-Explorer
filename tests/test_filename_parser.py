import unittest

from s_series_explorer.filename_parser import parse_filename


class FilenameParserTests(unittest.TestCase):
    def test_parses_dmc(self) -> None:
        parsed = parse_filename(
            "DMC-S1000DBIKE-AAA-DA0-00-00-00AA-041A-A_009-00_EN-US.xml"
        )
        self.assertEqual(parsed.object_type, "DMC")
        self.assertEqual(parsed.issue, "009")
        self.assertEqual(parsed.in_work, "00")
        self.assertEqual(parsed.language, "EN")
        self.assertEqual(parsed.country, "US")
        self.assertEqual(parsed.semantic_fields["infoCode"], "041")
        self.assertTrue(parsed.is_valid)

    def test_parses_user_icn_example(self) -> None:
        parsed = parse_filename(
            "ICN-A1CDE-A1-W068202-A-A1234-12345-A-002-01.des"
        )
        self.assertEqual(parsed.object_type, "ICN")
        self.assertEqual(parsed.code_segments[0], "A1CDE")
        self.assertEqual(parsed.code_segments[-1], "01")
        self.assertTrue(parsed.is_valid)

    def test_marks_human_errors(self) -> None:
        parsed = parse_filename("DMC-test--bad name.xml")
        self.assertFalse(parsed.is_valid)
        self.assertTrue(parsed.messages)


if __name__ == "__main__":
    unittest.main()
