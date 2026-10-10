"""Deterministic no-send preparation for fictional Apertus email drafts."""

import argparse
import json
import sys
from pathlib import Path
from typing import Any


SRC_DIR = Path(__file__).resolve().parent
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from policy import build_data_minimisation_record, build_model_context


DEFAULT_FIXTURE_PATH = Path(__file__).resolve().parents[1] / "data" / "test_contacts.json"


def load_fixture(path: Path) -> dict[str, Any]:
    """Load only the repository's fictional demo fixture."""
    return json.loads(path.read_text(encoding="utf-8"))


def find_fictional_contact(fixture: dict[str, Any], contact_id: str) -> dict[str, Any]:
    """Return one fictional contact or reject an unknown identifier."""
    for contact in fixture["contacts"]:
        if contact["id"] == contact_id:
            return contact
    raise ValueError(f"unknown fictional contact: {contact_id}")


def prepare_draft_request(
    fixture: dict[str, Any],
    contact_id: str,
) -> dict[str, Any]:
    """Create the only context that may later be sent to Apertus.

    This function deliberately does not call a model and has no send path.
    """
    campaign = fixture["campaign"]
    contact = find_fictional_contact(fixture, contact_id)

    return {
        "model_context": build_model_context(campaign, contact),
        "data_minimisation": build_data_minimisation_record(campaign, contact),
        "recipient": {
            "contact_id": contact["id"],
            "email": contact["email"],
        },
        "approval": {
            "status": "pending",
            "required_for": ["draft", "recipient", "purpose"],
        },
        "no_send": True,
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Prepare a fictional, no-send Apertus draft request."
    )
    parser.add_argument("--contact-id", required=True)
    parser.add_argument("--fixture", type=Path, default=DEFAULT_FIXTURE_PATH)
    args = parser.parse_args()

    result = prepare_draft_request(load_fixture(args.fixture), args.contact_id)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
