import importlib.util
from pathlib import Path
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "src" / "contact_review_queue.py"
CONTACTS_CSV = ROOT / "data" / "demo_contacts_3r.csv"


def load_module():
    spec = importlib.util.spec_from_file_location("contact_review_queue", MODULE_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError("contact review queue module cannot be loaded")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class ContactReviewQueueTests(unittest.TestCase):
    def setUp(self):
        self.module = load_module()
        self.contacts = self.module.load_demo_contacts(CONTACTS_CSV)
        self.temp_dir = tempfile.TemporaryDirectory()
        self.registry = self.module.ContactReviewRegistry(Path(self.temp_dir.name))

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_csv_overview_uses_exact_canonical_3r_counts(self):
        overview = self.module.contact_overview(self.contacts)

        self.assertEqual(overview, {"recruit": 17, "retain": 17, "recover": 16})

    def test_review_queue_snapshots_selected_contacts_without_email_addresses(self):
        queue = self.registry.create_queue(
            self.contacts,
            marketing_category="retain",
            campaign_goal="Neue Dienstleistung: Tassen bedrucken vorstellen",
        )

        self.assertEqual(queue["marketing_category"], "retain")
        self.assertEqual(queue["contact_count"], 17)
        self.assertTrue(queue["no_send"])
        self.assertEqual(queue["delivery_mode"], "draft_only")
        self.assertEqual(queue["current"]["position"], 1)
        self.assertEqual(queue["current"]["contact"]["contact_id"], "retain-001")
        self.assertEqual(queue["current"]["contact"]["first_name"], "Simon")
        self.assertNotIn("email", queue["current"]["contact"])
        self.assertNotIn("@example.invalid", str(queue))

    def test_next_and_previous_persist_the_current_review_position(self):
        queue = self.registry.create_queue(
            self.contacts,
            marketing_category="recover",
            campaign_goal="Neue Dienstleistung vorstellen",
        )

        moved = self.registry.next(queue["queue_id"])
        returned = self.registry.previous(queue["queue_id"])
        reloaded = self.registry.current(queue["queue_id"])

        self.assertEqual(moved["current"]["position"], 2)
        self.assertEqual(returned["current"]["position"], 1)
        self.assertEqual(reloaded["current"]["position"], 1)
        with self.assertRaisesRegex(ValueError, "already first"):
            self.registry.previous(queue["queue_id"])

    def test_reviewed_draft_can_be_replaced_and_confirmed_without_export(self):
        queue = self.registry.create_queue(
            self.contacts,
            marketing_category="recruit",
            campaign_goal="Neue Dienstleistung vorstellen",
        )
        draft = (
            "Betreff: Neu bei Onlineshop Demo AG\n\n"
            "Sehr geehrte Frau Meier,\n\n"
            "wir stellen Ihnen heute unsere neue Dienstleistung vor.\n\n"
            "Freundliche Grüsse\nOnlineshop Demo AG"
        )

        updated = self.registry.replace_draft(queue["queue_id"], draft)
        confirmed = self.registry.confirm_current(queue["queue_id"])

        self.assertEqual(updated["current"]["status"], "needs_review")
        self.assertEqual(updated["current"]["draft"], draft)
        self.assertEqual(confirmed["current"]["status"], "confirmed")
        self.assertTrue(confirmed["no_send"])
        self.assertNotIn("export", confirmed)


if __name__ == "__main__":
    unittest.main()
