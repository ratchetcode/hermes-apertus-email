import sys
from pathlib import Path
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from conversation_state import ConversationStateMachine


class ConversationStateMachineTests(unittest.TestCase):
    def setUp(self):
        self.flow = ConversationStateMachine()

    def test_language_is_asked_once_then_each_3r_field_advances_one_step(self):
        first = self.flow.advance("session-1", "hallo")
        self.assertEqual(first["state"], "language")
        self.assertIn("Welche Sprache", first["reply"])

        language = self.flow.advance("session-1", "deutsch")
        self.assertEqual(language["state"], "workflow")
        self.assertIn("Was möchten Sie vorbereiten", language["reply"])

        workflow = self.flow.advance("session-1", "3R-Kampagne")
        self.assertEqual(workflow["state"], "category")
        self.assertIn("Kategorie", workflow["reply"])

        category = self.flow.advance("session-1", "retain")
        self.assertEqual(category["state"], "goal")
        self.assertNotIn("Ton", category["reply"])

        goal = self.flow.advance("session-1", "Reaktivierung mit fiktivem Angebot")
        self.assertEqual(goal["state"], "tone")
        self.assertIn("Ton", goal["reply"])

        completed = self.flow.advance("session-1", "sachlich")
        self.assertEqual(completed["state"], "approval")
        self.assertEqual(completed["action"]["kind"], "segment_preflight")
        self.assertEqual(completed["action"]["arguments"]["marketing_category"], "retain")
        self.assertEqual(completed["action"]["arguments"]["language"], "Deutsch")

    def test_explicit_yes_advances_only_after_preflight_and_can_request_export(self):
        self.flow.advance("session-3", "hallo")
        self.flow.advance("session-3", "Deutsch")
        self.flow.advance("session-3", "3R")
        self.flow.advance("session-3", "recover")
        self.flow.advance("session-3", "Reaktivierung")
        preflight = self.flow.advance("session-3", "sachlich")
        self.assertEqual(preflight["action"]["kind"], "segment_preflight")
        self.flow.bind_approval("session-3", "approval-1")

        approved = self.flow.advance("session-3", "ja")
        self.assertEqual(approved["action"]["kind"], "approve_and_generate")
        self.assertEqual(approved["action"]["arguments"]["approval_id"], "approval-1")
        self.flow.mark_drafts_ready("session-3")
        export = self.flow.advance("session-3", "ja")
        self.assertEqual(export["action"]["kind"], "export")

    def test_yes_is_not_accepted_as_campaign_category(self):
        self.flow.advance("session-2", "hallo")
        self.flow.advance("session-2", "Deutsch")
        self.flow.advance("session-2", "3R")

        result = self.flow.advance("session-2", "ja")

        self.assertEqual(result["state"], "category")
        self.assertIn("recruit", result["reply"])


if __name__ == "__main__":
    unittest.main()
