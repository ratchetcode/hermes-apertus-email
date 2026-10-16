from pathlib import Path
import subprocess
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
REPORT_SOURCE = ROOT / "technical_report.md"
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
        self.assertIn(b"42/42", pdf)


if __name__ == "__main__":
    unittest.main()
