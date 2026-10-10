import importlib.util
import json
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
FIXTURE_PATH = ROOT / "data" / "test_contacts.json"
WORKFLOW_PATH = ROOT / "src" / "workflow.py"


def load_workflow_module():
    spec = importlib.util.spec_from_file_location("workflow", WORKFLOW_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError("workflow module cannot be loaded")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class DraftPreparationTests(unittest.TestCase):
    def setUp(self):
        self.fixture = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
        self.workflow = load_workflow_module()

    def test_prepare_draft_request_exposes_only_minimised_model_context(self):
        result = self.workflow.prepare_draft_request(
            self.fixture,
            "demo-contact-001",
        )

        self.assertEqual(result["model_context"], {
            "purpose": "Invitation to a fictional workshop on responsible AI workflows",
            "contact": {
                "first_name": "Mara",
                "company": "Alpenlicht Studio",
                "industry": "Design",
                "interest": "AI-supported content workflows",
            },
        })
        self.assertEqual(result["data_minimisation"]["excluded_fields"], [
            "email",
            "id",
            "internal_note",
        ])
        self.assertNotIn("email", result["model_context"]["contact"])
        self.assertTrue(result["no_send"])

    def test_prepare_draft_request_requires_pending_human_approval(self):
        result = self.workflow.prepare_draft_request(
            self.fixture,
            "demo-contact-001",
        )

        self.assertEqual(result["approval"], {
            "status": "pending",
            "required_for": ["draft", "recipient", "purpose"],
        })
        self.assertEqual(result["recipient"], {
            "contact_id": "demo-contact-001",
            "email": "mara@example.invalid",
        })

    def test_prepare_draft_request_rejects_unknown_contact(self):
        with self.assertRaisesRegex(ValueError, "unknown fictional contact"):
            self.workflow.prepare_draft_request(self.fixture, "not-a-contact")


if __name__ == "__main__":
    unittest.main()
