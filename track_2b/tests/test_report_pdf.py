from pathlib import Path
import subprocess
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
REPORT_SOURCE = ROOT / "technical_report_de.md"
REPORT_SOURCE_EN = ROOT / "technical_report_en.md"
OFFICIAL_PROJECT_NAME = b"Hermes Agent x Apertus for privacy-conscious email marketing"
GENERATOR = ROOT / "docs" / "create_report_pdf.py"


class TechnicalReportPdfTests(unittest.TestCase):
    def test_generator_creates_a_four_page_report_with_a_visible_workflow(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            output = Path(temporary_directory) / "report.pdf"
            completed = subprocess.run(
                ["python3", str(GENERATOR), str(REPORT_SOURCE), str(output)],
                check=True,
                capture_output=True,
                text=True,
            )
            pdf = output.read_bytes()

        self.assertIn("4 page(s)".encode(), completed.stdout.encode())
        self.assertEqual(pdf.count(b"/Type /Page "), 4)
        self.assertIn(b"Workflow", pdf)
        self.assertIn(b"Kein Versand", pdf)
        self.assertIn(OFFICIAL_PROJECT_NAME, pdf)
        self.assertNotIn(b"Apertus Draft Gate", pdf)
        self.assertNotIn(b"?", pdf)
        self.assertIn(b"E-Mail-Automation", pdf)
        self.assertIn(b"README.md", pdf)
        self.assertIn(b"43/43", pdf)

    def test_generator_creates_an_english_four_page_report(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            output = Path(temporary_directory) / "report-en.pdf"
            completed = subprocess.run(
                ["python3", str(GENERATOR), "--language", "en", str(REPORT_SOURCE_EN), str(output)],
                check=True,
                capture_output=True,
                text=True,
            )
            pdf = output.read_bytes()

        self.assertIn("4 page(s)".encode(), completed.stdout.encode())
        self.assertEqual(pdf.count(b"/Type /Page "), 4)
        self.assertIn(b"controlled workflow", pdf)
        self.assertIn(b"No sending", pdf)
        self.assertIn(OFFICIAL_PROJECT_NAME, pdf)
        self.assertNotIn(b"Apertus Draft Gate", pdf)
        self.assertNotIn(b"?", pdf)
        self.assertIn(b"Email automation can mix", pdf)
        self.assertIn(b"README.md", pdf)
        self.assertIn(b"43/43", pdf)


if __name__ == "__main__":
    unittest.main()
