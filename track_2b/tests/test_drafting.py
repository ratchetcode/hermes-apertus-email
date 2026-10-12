import contextlib
import importlib.util
import io
import json
import os
from pathlib import Path
import sys
import unittest


ROOT = Path(__file__).resolve().parents[1]
WORKFLOW_PATH = ROOT / "src" / "workflow.py"


def load_workflow_module():
    spec = importlib.util.spec_from_file_location("workflow", WORKFLOW_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError("workflow module cannot be loaded")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class ApertusDraftTests(unittest.TestCase):
    def setUp(self):
        self.workflow = load_workflow_module()
        self.fixture = json.loads(
            (ROOT / "data" / "test_contacts.json").read_text(encoding="utf-8")
        )
        self.preflight = self.workflow.prepare_draft_request(
            self.fixture, "demo-contact-001"
        )

    def test_generate_draft_sends_only_minimised_context_to_model(self):
        captured = {}

        def fake_post_json(url, headers, payload, timeout_seconds):
            captured.update(
                {
                    "url": url,
                    "headers": headers,
                    "payload": payload,
                    "timeout_seconds": timeout_seconds,
                }
            )
            return {
                "choices": [
                    {
                        "message": {
                            "content": "Betreff: Einladung\n\nHallo Mara,\n\nwir laden Sie herzlich ein."
                        }
                    }
                ]
            }

        result = self.workflow.generate_draft(
            self.preflight,
            model_name="swiss-ai/Apertus-v1.5-8B",
            base_url="https://example.test/v1/",
            api_key="test-key",
            post_json=fake_post_json,
        )

        payload_text = json.dumps(captured["payload"], ensure_ascii=False)
        self.assertEqual(captured["url"], "https://example.test/v1/chat/completions")
        self.assertEqual(captured["headers"]["Authorization"], "Bearer test-key")
        self.assertEqual(captured["payload"]["model"], "swiss-ai/Apertus-v1.5-8B")
        self.assertNotIn("mara@example.invalid", payload_text)
        self.assertNotIn("demo-contact-001", payload_text)
        self.assertNotIn("Not approved for model use", payload_text)
        self.assertEqual(result["draft"], "Betreff: Einladung\n\nHallo Mara,\n\nwir laden Sie herzlich ein.")
        self.assertTrue(result["no_send"])
        self.assertEqual(result["approval"]["status"], "pending")

    def test_generate_draft_rejects_an_invalid_model_response(self):
        def fake_post_json(*_args):
            return {"choices": []}

        with self.assertRaisesRegex(ValueError, "no draft content"):
            self.workflow.generate_draft(
                self.preflight,
                model_name="swiss-ai/Apertus-v1.5-8B",
                base_url="https://example.test/v1",
                api_key="test-key",
                post_json=fake_post_json,
            )
    def test_live_cli_returns_a_clean_error_record_when_model_generation_fails(self):
        original_argv = sys.argv
        original_generate_draft = self.workflow.generate_draft
        original_environment = os.environ.copy()
        stdout = io.StringIO()
        try:
            sys.argv = ["workflow.py", "--contact-id", "demo-contact-001", "--live"]
            os.environ.update(
                {
                    "LLM_NAME": "swiss-ai/Apertus-v1.5-8B",
                    "LLM_BASE_URL": "https://example.test/v1",
                    "LLM_API_KEY": "test-key",
                }
            )

            def failing_generate_draft(*_args, **_kwargs):
                raise RuntimeError("model endpoint returned HTTP 403")

            self.workflow.generate_draft = failing_generate_draft
            with contextlib.redirect_stdout(stdout):
                exit_code = self.workflow.main()
        finally:
            sys.argv = original_argv
            self.workflow.generate_draft = original_generate_draft
            os.environ.clear()
            os.environ.update(original_environment)

        result = json.loads(stdout.getvalue())
        self.assertEqual(exit_code, 2)
        self.assertEqual(result["error"], {
            "stage": "draft_generation",
            "message": "model endpoint returned HTTP 403",
        })
        self.assertTrue(result["no_send"])
        self.assertEqual(result["approval"]["status"], "pending")


if __name__ == "__main__":
    unittest.main()
