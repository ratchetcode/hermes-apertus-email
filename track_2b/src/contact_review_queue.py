"""Deterministic local review queues for fictional CSV email drafts.

The queue snapshots only approved presentation fields for a selected 3R cohort.
It has no transport, recipient-address, CRM, webhook, or export capability.
"""

from __future__ import annotations

import csv
import json
import uuid
from pathlib import Path
from typing import Any

MARKETING_CATEGORIES = ("recruit", "retain", "recover")
DELIVERY_MODE = "draft_only"
_ALLOWED_CONTACT_FIELDS = (
    "contact_id", "first_name", "last_name", "company", "language",
    "marketing_category", "lifecycle_stage", "interest", "campaign_tags",
)


def load_demo_contacts(csv_path: Path) -> list[dict[str, str]]:
    """Load and validate the sole visible fictional contact source."""
    with csv_path.open(encoding="utf-8", newline="") as handle:
        contacts = list(csv.DictReader(handle))
    if not contacts:
        raise ValueError("fictional demo contact CSV is empty")
    required = set(_ALLOWED_CONTACT_FIELDS) | {"email", "consent_status", "unsubscribed"}
    if not required.issubset(contacts[0]):
        raise ValueError("fictional demo contact CSV has missing fields")
    for contact in contacts:
        if contact.get("marketing_category") not in MARKETING_CATEGORIES:
            raise ValueError("unsupported marketing category in fictional demo contacts")
        if not contact.get("email", "").endswith("@example.invalid"):
            raise ValueError("fictional demo contacts require example.invalid addresses")
        if contact.get("consent_status") != "fictional_demo_only":
            raise ValueError("contact is not marked as fictional demo data")
        if contact.get("unsubscribed") != "false":
            raise ValueError("fictional demo queue excludes unsubscribed contacts")
    return contacts


def contact_overview(contacts: list[dict[str, str]]) -> dict[str, int]:
    """Return exact counts in the canonical 3R category order."""
    counts = {category: 0 for category in MARKETING_CATEGORIES}
    for contact in contacts:
        category = contact.get("marketing_category")
        if category not in counts:
            raise ValueError("unsupported marketing category in fictional demo contacts")
        counts[category] += 1
    return counts


def contacts_for_category(contacts: list[dict[str, str]], marketing_category: str) -> list[dict[str, str]]:
    """Select one ordered fictional 3R cohort without exposing its addresses."""
    if marketing_category not in MARKETING_CATEGORIES:
        raise ValueError("unsupported marketing category")
    selected = [contact for contact in contacts if contact["marketing_category"] == marketing_category]
    if not selected:
        raise ValueError("no fictional contacts in marketing category")
    return selected


def _contact_snapshot(contact: dict[str, str]) -> dict[str, str]:
    return {field: contact[field] for field in _ALLOWED_CONTACT_FIELDS}


class ContactReviewRegistry:
    """Persistent no-send, per-contact draft review state in the Hermes runtime."""

    def __init__(self, state_dir: Path):
        self.state_dir = state_dir
        self.state_file = state_dir / "contact-review-queues.json"

    def _load(self) -> dict[str, dict[str, Any]]:
        if not self.state_file.exists():
            return {}
        records = json.loads(self.state_file.read_text(encoding="utf-8"))
        if not isinstance(records, dict):
            raise ValueError("invalid local contact review registry")
        return records

    def _save(self, records: dict[str, dict[str, Any]]) -> None:
        self.state_dir.mkdir(parents=True, exist_ok=True)
        temporary = self.state_file.with_suffix(".tmp")
        temporary.write_text(json.dumps(records, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
        temporary.replace(self.state_file)

    @staticmethod
    def _operator_view(record: dict[str, Any]) -> dict[str, Any]:
        position = int(record["current_index"]) + 1
        item = record["items"][position - 1]
        return {
            "queue_id": record["queue_id"],
            "marketing_category": record["marketing_category"],
            "campaign_goal": record["campaign_goal"],
            "contact_count": record["contact_count"],
            "current": {
                "position": position,
                "total": record["contact_count"],
                "contact": item["contact"],
                "status": item["status"],
                "draft": item.get("draft"),
            },
            "review_actions": ["next", "previous", "replace_draft", "confirm", "skip", "abort"],
            "delivery_mode": DELIVERY_MODE,
            "no_send": True,
        }

    def create_queue(self, contacts: list[dict[str, str]], *, marketing_category: str, campaign_goal: str) -> dict[str, Any]:
        if not campaign_goal.strip():
            raise ValueError("campaign goal is required")
        selected = contacts_for_category(contacts, marketing_category)
        queue_id = f"review-{uuid.uuid4().hex[:12]}"
        record = {
            "queue_id": queue_id,
            "marketing_category": marketing_category,
            "campaign_goal": campaign_goal.strip(),
            "contact_count": len(selected),
            "current_index": 0,
            "items": [
                {"contact": _contact_snapshot(contact), "status": "not_created", "draft": None}
                for contact in selected
            ],
            "delivery_mode": DELIVERY_MODE,
            "no_send": True,
        }
        records = self._load()
        records[queue_id] = record
        self._save(records)
        return self._operator_view(record)

    def _get(self, queue_id: str) -> tuple[dict[str, dict[str, Any]], dict[str, Any]]:
        records = self._load()
        record = records.get(queue_id)
        if record is None:
            raise ValueError("unknown review queue")
        if record.get("delivery_mode") != DELIVERY_MODE or not record.get("no_send"):
            raise ValueError("draft-only review queue is required")
        return records, record

    def current(self, queue_id: str) -> dict[str, Any]:
        _records, record = self._get(queue_id)
        return self._operator_view(record)

    def next(self, queue_id: str) -> dict[str, Any]:
        records, record = self._get(queue_id)
        if record["current_index"] >= record["contact_count"] - 1:
            raise ValueError("already last review item")
        record["current_index"] += 1
        self._save(records)
        return self._operator_view(record)

    def previous(self, queue_id: str) -> dict[str, Any]:
        records, record = self._get(queue_id)
        if record["current_index"] <= 0:
            raise ValueError("already first review item")
        record["current_index"] -= 1
        self._save(records)
        return self._operator_view(record)

    def replace_draft(self, queue_id: str, draft: str) -> dict[str, Any]:
        if not draft.strip():
            raise ValueError("draft must not be empty")
        records, record = self._get(queue_id)
        item = record["items"][record["current_index"]]
        item["draft"] = draft.strip()
        item["status"] = "needs_review"
        self._save(records)
        return self._operator_view(record)

    def confirm_current(self, queue_id: str) -> dict[str, Any]:
        records, record = self._get(queue_id)
        item = record["items"][record["current_index"]]
        if not item.get("draft"):
            raise ValueError("a draft is required before confirmation")
        item["status"] = "confirmed"
        self._save(records)
        return self._operator_view(record)

    def skip_current(self, queue_id: str) -> dict[str, Any]:
        records, record = self._get(queue_id)
        record["items"][record["current_index"]]["status"] = "skipped"
        self._save(records)
        return self._operator_view(record)

    def abort(self, queue_id: str) -> dict[str, Any]:
        records, record = self._get(queue_id)
        record["status"] = "aborted"
        self._save(records)
        return self._operator_view(record)
