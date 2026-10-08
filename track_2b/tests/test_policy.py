import importlib.util
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
FIXTURE_PATH = ROOT / "data" / "test_contacts.json"
POLICY_PATH = ROOT / "src" / "policy.py"

def load_policy_module():
    if not POLICY_PATH.exists():
        return None

    spec = importlib.util.spec_from_file_location("policy", POLICY_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

class ModelContextPolicyTests(unittest.TestCase):
    def test_build_model_context_uses_only_approved_contact_fields(self):
        fixture = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
        campaign = fixture["campaign"]
        contact = fixture["contacts"][0]

        policy = load_policy_module()

        self.assertIsNotNone(
            policy,
            "src/policy.py is missing — build_model_context must be implemented.",
        )
        self.assertTrue(
            hasattr(policy, "build_model_context"),
            "build_model_context is missing from src/policy.py.",
        )

        result = policy.build_model_context(campaign, contact)

        self.assertEqual(
            result,
            {
                "purpose": "Invitation to a fictional workshop on responsible AI workflows",
                "contact": {
                    "first_name": "Mara",
                    "company": "Alpenlicht Studio",
                    "industry": "Design",
                    "interest": "AI-supported content workflows",
                },
            },
        )
        self.assertNotIn("email", result["contact"])
        self.assertNotIn("internal_note", result["contact"])
        self.assertNotIn("id", result["contact"])

    def test_build_model_context_rejects_forbidden_fields_even_if_listed(self):
        fixture = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
        campaign = dict(fixture["campaign"])
        contact = fixture["contacts"][0]

        campaign["approved_fields"] = [
            *campaign["approved_fields"],
            "email",
        ]

        policy = load_policy_module()

        with self.assertRaisesRegex(ValueError, "forbidden"):
            policy.build_model_context(campaign, contact)

    def test_data_minimisation_record_lists_used_and_excluded_fields(self):
        fixture = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
        campaign = fixture["campaign"]
        contact = fixture["contacts"][0]

        policy = load_policy_module()

        result = policy.build_data_minimisation_record(campaign, contact)

        self.assertEqual(
            result,
            {
                "used_fields": [
                    "first_name",
                    "company",
                    "industry",
                    "interest",
                ],
                "excluded_fields": [
                    "email",
                    "id",
                    "internal_note",
                ],
            },
        )
