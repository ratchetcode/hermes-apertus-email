import importlib.util
import json
from pathlib import Path
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "src" / "segment_queue.py"
FIXTURE_PATH = ROOT / "data" / "test_contacts.json"


def load_module():
    spec = importlib.util.spec_from_file_location("segment_queue", MODULE_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError("segment queue module cannot be loaded")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class SegmentQueueTests(unittest.TestCase):
    def setUp(self):
        self.module = load_module()
        self.fixture = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
        self.temp_dir = tempfile.TemporaryDirectory()
        self.registry = self.module.SegmentDraftRegistry(Path(self.temp_dir.name))

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_demo_fixture_has_eight_fictional_contacts_per_3r_category(self):
        counts = self.module.category_counts(self.fixture)

        self.assertEqual(counts, {"recruit": 8, "retain": 8, "recover": 8})

    def test_segment_preflight_builds_eight_minimised_no_send_drafts(self):
        preflight = self.module.prepare_segment_preflight(
            self.fixture,
            marketing_category="recruit",
            campaign_goal="Fiktives Willkommensangebot vorstellen",
            language="de",
            tone="freundlich und sachlich",
        )

        self.assertEqual(preflight["marketing_category"], "recruit")
        self.assertEqual(preflight["contact_count"], 8)
        self.assertTrue(preflight["no_send"])
        self.assertEqual(preflight["delivery_mode"], "draft_only")
        self.assertEqual(len(preflight["drafts"]), 8)
        for draft in preflight["drafts"]:
            payload = json.dumps(draft["model_context"], ensure_ascii=False)
            self.assertNotIn("@example.invalid", payload)
            self.assertNotIn("internal_note", payload)
            self.assertEqual(draft["status"], "queued")

    def test_segment_preflight_rejects_unknown_category(self):
        with self.assertRaisesRegex(ValueError, "unsupported marketing category"):
            self.module.prepare_segment_preflight(
                self.fixture,
                marketing_category="lead",
                campaign_goal="Test",
                language="de",
                tone="sachlich",
            )

    def test_operator_can_approve_a_queue_once_without_a_send_path(self):
        preflight = self.module.prepare_segment_preflight(
            self.fixture,
            marketing_category="recover",
            campaign_goal="Fiktive Reaktivierung vorbereiten",
            language="de",
            tone="freundlich",
        )
        record = self.registry.create_preflight(preflight)

        approved = self.registry.approve(record["approval_id"])
        claimed = self.registry.claim_for_generation(record["approval_id"])

        self.assertEqual(approved["approval"]["status"], "approved_for_batch_generation")
        self.assertEqual(claimed["approval"]["status"], "generation_claimed")
        self.assertTrue(claimed["no_send"])
        self.assertEqual(claimed["delivery_mode"], "draft_only")
        with self.assertRaisesRegex(ValueError, "not approved"):
            self.registry.claim_for_generation(record["approval_id"])

    def test_generated_drafts_are_logged_without_any_send_event(self):
        preflight = self.module.prepare_segment_preflight(
            self.fixture,
            marketing_category="retain",
            campaign_goal="Fiktive Kundeninformation vorbereiten",
            language="de",
            tone="sachlich",
        )
        record = self.registry.create_preflight(preflight)
        self.registry.approve(record["approval_id"])
        self.registry.claim_for_generation(record["approval_id"])

        result = self.registry.record_generated_drafts(
            record["approval_id"],
            [f"Betreff: Entwurf {index}" for index in range(1, 9)],
        )

        self.assertTrue(result["no_send"])
        self.assertEqual(result["delivery_mode"], "draft_only")
        self.assertTrue(all(item["status"] == "needs_review" for item in result["drafts"]))
        events = json.loads(self.registry.events_file.read_text(encoding="utf-8"))
        event_types = [event["event_type"] for event in events]
        self.assertIn("drafts_created", event_types)
        self.assertNotIn("sent", event_types)


if __name__ == "__main__":
    unittest.main()
