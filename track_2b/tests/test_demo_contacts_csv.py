import csv
from collections import Counter
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
CONTACTS_CSV = ROOT / "data" / "demo_contacts_3r.csv"
PROFILE_SOUL = ROOT / "agent-profile" / "SOUL.md"
CATEGORY_ORDER = ("recruit", "retain", "recover")


class DemoContactsCsvTests(unittest.TestCase):
    def test_fictional_demo_contacts_are_limited_to_fifty_and_grouped_by_3r(self):
        with CONTACTS_CSV.open(newline="", encoding="utf-8") as handle:
            contacts = list(csv.DictReader(handle))

        self.assertEqual(len(contacts), 50)
        self.assertEqual(
            Counter(contact["marketing_category"] for contact in contacts),
            {"recruit": 17, "retain": 17, "recover": 16},
        )
        category_positions = [CATEGORY_ORDER.index(contact["marketing_category"]) for contact in contacts]
        self.assertEqual(category_positions, sorted(category_positions))
        self.assertTrue(all(contact["email"].endswith("@example.invalid") for contact in contacts))
        self.assertTrue(all(contact["consent_status"] == "fictional_demo_only" for contact in contacts))

    def test_profile_soul_points_only_to_the_fictional_demo_contact_csv(self):
        soul = PROFILE_SOUL.read_text(encoding="utf-8")

        self.assertIn("/workspace/data/demo_contacts_3r.csv", soul)
        self.assertIn("keine reale Kundendatenbank", soul)


if __name__ == "__main__":
    unittest.main()
