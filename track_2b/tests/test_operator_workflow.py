import sys
from pathlib import Path
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from operator_workflow import run_console
from workflow import load_fixture


class OperatorWorkflowTests(unittest.TestCase):
    def test_german_3r_workflow_exports_eight_review_drafts_without_shipping_text(self):
        answers = iter([
            "deutsch", "3 R", "retain", "10% Onlineshop-Gutschein", "freundlich", "ja", "ja"
        ])
        output = []
        fixture = load_fixture(Path(__file__).resolve().parents[1] / "data" / "test_contacts.json")

        with tempfile.TemporaryDirectory() as directory:
            result = run_console(
                input_fn=lambda _prompt: next(answers),
                output_fn=output.append,
                fixture=fixture,
                state_dir=Path(directory),
                generate_fn=lambda _preflight: {"draft": "Betreff: Fiktiver Entwurf\n\nNur zur Prüfung."},
            )
            self.assertTrue(result["exported"])
            self.assertEqual(result["draft_count"], 8)
            self.assertTrue((Path(result["export_dir"]) / "manifest.json").exists())

        rendered = "\n".join(output)
        self.assertIn("Ausgewählte fiktive Kontakte (8)", rendered)
        self.assertNotIn("Versand", rendered)
        self.assertNotIn("Which", rendered)


if __name__ == "__main__":
    unittest.main()
