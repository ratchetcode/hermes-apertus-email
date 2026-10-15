import importlib.util
import json
import os
from pathlib import Path
import tempfile
import unittest
from email import policy
from email.parser import BytesParser


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "src" / "email_framework.py"
PLUGIN_PATH = ROOT / ".hermes" / "plugins" / "email-framework" / "plugin.yaml"


def load_module():
    spec = importlib.util.spec_from_file_location("email_framework", MODULE_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError("email framework module cannot be loaded")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class EmailFrameworkRegistryTests(unittest.TestCase):
    def setUp(self):
        self.module = load_module()
        self.fixture = json.loads(
            (ROOT / "data" / "test_contacts.json").read_text(encoding="utf-8")
        )
        self.preflight = self.module.prepare_draft_request(
            self.fixture, "demo-contact-001"
        )
        self.temp_dir = tempfile.TemporaryDirectory()
        self.registry = self.module.DraftRegistry(Path(self.temp_dir.name))

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_preflight_creates_pending_no_send_approval_record(self):
        record = self.registry.create_preflight(
            self.preflight,
            workflow_type="newsletter",
        )

        self.assertEqual(record["workflow_type"], "newsletter")
        self.assertEqual(record["approval"]["status"], "pending_operator_approval")
        self.assertTrue(record["no_send"])
        self.assertNotIn("email", record["model_context"]["contact"])
        self.assertTrue(record["approval_id"])

    def test_generate_refuses_a_preflight_without_slash_command_approval(self):
        record = self.registry.create_preflight(
            self.preflight,
            workflow_type="newsletter",
        )

        with self.assertRaisesRegex(ValueError, "not approved"):
            self.registry.claim_for_generation(record["approval_id"])

    def test_operator_approval_can_be_claimed_only_once(self):
        record = self.registry.create_preflight(
            self.preflight,
            workflow_type="follow_up",
            parent_draft_id="draft-demo-001",
        )

        approved = self.registry.approve(record["approval_id"])
        claimed = self.registry.claim_for_generation(record["approval_id"])

        self.assertEqual(approved["approval"]["status"], "approved_for_one_draft")
        self.assertEqual(claimed["approval"]["status"], "generation_claimed")
        self.assertEqual(claimed["parent_draft_id"], "draft-demo-001")
        with self.assertRaisesRegex(ValueError, "not approved"):
            self.registry.claim_for_generation(record["approval_id"])


class EmailFrameworkPluginContractTests(unittest.TestCase):
    def test_plugin_declares_safe_preflight_and_approved_generation_tools(self):
        manifest = PLUGIN_PATH.read_text(encoding="utf-8")

        self.assertIn("name: email-framework", manifest)
        self.assertIn("email_framework_preflight", manifest)
        self.assertIn("email_framework_segment_preflight", manifest)
        self.assertIn("email_framework_generate_approved_draft", manifest)
        self.assertIn("email_framework_generate_segment_drafts", manifest)


class SegmentPluginFlowTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.previous_environment = {
            key: os.environ.get(key)
            for key in ("EMAIL_FRAMEWORK_WORKSPACE", "HERMES_HOME", "LLM_NAME", "LLM_BASE_URL", "LLM_API_KEY")
        }
        os.environ.update(
            {
                "EMAIL_FRAMEWORK_WORKSPACE": str(ROOT),
                "HERMES_HOME": self.temp_dir.name,
                "LLM_NAME": "fake-model",
                "LLM_BASE_URL": "https://example.invalid/v1",
                "LLM_API_KEY": "fake-key",
            }
        )
        plugin_path = ROOT / ".hermes" / "plugins" / "email-framework" / "__init__.py"
        spec = importlib.util.spec_from_file_location("email_framework_plugin_test", plugin_path)
        if spec is None or spec.loader is None:
            raise RuntimeError("email framework plugin cannot be loaded")
        self.plugin = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.plugin)

    def tearDown(self):
        for key, value in self.previous_environment.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value
        self.temp_dir.cleanup()

    def test_segment_flow_creates_eight_review_drafts_with_a_fake_model(self):
        preflight = json.loads(
            self.plugin._segment_preflight(
                {
                    "marketing_category": "recruit",
                    "campaign_goal": "Fiktives Willkommensangebot vorstellen",
                    "language": "de",
                    "tone": "freundlich",
                }
            )
        )
        self.assertTrue(preflight["success"])
        self.assertEqual(preflight["contact_count"], 8)
        self.assertTrue(preflight["no_send"])

        approval = json.loads(self.plugin._approve_segment(preflight["approval_id"]))
        self.assertEqual(approval["approval"]["status"], "approved_for_batch_generation")

        self.plugin.generate_draft = lambda preflight, **_kwargs: {
            **preflight,
            "draft": "Betreff: Fiktiver Entwurf\n\nDies ist nur ein Entwurf.",
        }
        result = json.loads(
            self.plugin._generate_segment_drafts({"approval_id": preflight["approval_id"]})
        )

        self.assertTrue(result["success"])
        self.assertTrue(result["no_send"])
        self.assertEqual(result["delivery_mode"], "draft_only")
        self.assertEqual(len(result["drafts"]), 8)
        self.assertTrue(all(item["status"] == "needs_review" for item in result["drafts"]))
        self.assertTrue(all("@example.invalid" not in json.dumps(item["model_context"]) for item in result["drafts"]))

    def test_segment_commands_bypass_unreliable_model_tool_call_text(self):
        preflight = json.loads(
            self.plugin._segment_preflight_command(
                json.dumps(
                    {
                        "marketing_category": "recover",
                        "campaign_goal": "reaktivierung",
                        "language": "Deutsch",
                        "tone": "sachlich",
                    }
                )
            )
        )

        self.assertTrue(preflight["success"])
        self.assertEqual(preflight["contact_count"], 8)
        approval = json.loads(self.plugin._approve_segment(preflight["approval_id"]))
        self.assertEqual(approval["approval"]["status"], "approved_for_batch_generation")

        self.plugin.generate_draft = lambda preflight, **_kwargs: {**preflight, "draft": "Entwurf"}
        result = json.loads(self.plugin._generate_segment_command(preflight["approval_id"]))

        self.assertTrue(result["success"])
        self.assertTrue(result["no_send"])
        self.assertEqual(len(result["drafts"]), 8)

    def test_conversation_admission_consumes_input_and_uses_selected_language(self):
        session_id = "test-deterministic-conversation"
        first = self.plugin._conversation_admission(
            text="hallo", session_key=session_id, platform="gateway", source={}, message_id="1"
        )
        self.assertEqual(first, {"action": "handled", "reply": "Welche Sprache möchten Sie verwenden? [Deutsch / English / Français]"})

        selected = self.plugin._conversation_admission(
            text="deutsch", session_key=session_id, platform="gateway", source={}, message_id="2"
        )
        self.assertIn("Was möchten Sie vorbereiten?", selected["reply"])
        self.assertNotIn("What would", selected["reply"])
        self.assertNotIn("Que souhaitez", selected["reply"])

    def test_export_command_writes_eight_importable_draft_only_eml_files(self):
        preflight = json.loads(
            self.plugin._segment_preflight(
                {
                    "marketing_category": "retain",
                    "campaign_goal": "Reaktivierung mit einem fiktiven Angebot",
                    "language": "Deutsch",
                    "tone": "sachlich",
                }
            )
        )
        json.loads(self.plugin._approve_segment(preflight["approval_id"]))
        self.plugin.generate_draft = lambda preflight, **_kwargs: {
            **preflight,
            "draft": "Betreff: Fiktiver Entwurf\n\nDies ist nur ein fiktiver Entwurf.",
        }
        json.loads(self.plugin._generate_segment_command(preflight["approval_id"]))

        exported = json.loads(self.plugin._export_segment_command(preflight["approval_id"]))

        self.assertTrue(exported["success"])
        self.assertTrue(exported["no_send"])
        self.assertEqual(exported["draft_count"], 8)
        export_dir = Path(exported["export_dir"])
        eml_files = sorted(export_dir.glob("*.eml"))
        self.assertEqual(len(eml_files), 8)
        message = BytesParser(policy=policy.default).parsebytes(eml_files[0].read_bytes())
        self.assertEqual(message["Subject"], "Fiktiver Entwurf")
        self.assertTrue(message["To"].endswith("@example.invalid"))
        self.assertEqual(message["X-Draft-Only"], "true")
        self.assertNotIn("internal_note", eml_files[0].read_text(encoding="utf-8"))
        manifest = json.loads((export_dir / "manifest.json").read_text(encoding="utf-8"))
        self.assertEqual(manifest["status"], "needs_review")
        self.assertEqual(len(manifest["drafts"]), 8)


if __name__ == "__main__":
    unittest.main()
