"""Controlled no-send queues for the fictional Recruit/Retain/Recover demo."""

from __future__ import annotations

import json
import sys
import uuid
from pathlib import Path
from typing import Any


SRC_DIR = Path(__file__).resolve().parent
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from policy import build_data_minimisation_record, build_model_context


MARKETING_CATEGORIES = ("recruit", "retain", "recover")
DELIVERY_MODE = "draft_only"


def category_counts(fixture: dict[str, Any]) -> dict[str, int]:
    """Return counts for the only supported fictional 3R categories."""
    counts = {category: 0 for category in MARKETING_CATEGORIES}
    for contact in fixture["contacts"]:
        category = contact.get("marketing_category")
        if category not in counts:
            raise ValueError("unsupported marketing category in fictional fixture")
        counts[category] += 1
    return counts


def _contacts_for_category(fixture: dict[str, Any], marketing_category: str) -> list[dict[str, Any]]:
    if marketing_category not in MARKETING_CATEGORIES:
        raise ValueError("unsupported marketing category")
    contacts = [
        contact
        for contact in fixture["contacts"]
        if contact["marketing_category"] == marketing_category
    ]
    if not contacts:
        raise ValueError("no fictional contacts in marketing category")
    return contacts


def _campaign_for_segment(
    marketing_category: str,
    campaign_goal: str,
    language: str,
    tone: str,
) -> dict[str, Any]:
    if not campaign_goal.strip() or not language.strip() or not tone.strip():
        raise ValueError("campaign goal, language and tone are required")
    return {
        "purpose": campaign_goal.strip(),
        "approved_fields": [
            "first_name",
            "last_name",
            "company",
            "industry",
            "interest",
            "marketing_category",
            "language",
            "offer_category",
        ],
        "marketing_category": marketing_category,
        "language": language.strip(),
        "tone": tone.strip(),
    }


def prepare_segment_preflight(
    fixture: dict[str, Any],
    *,
    marketing_category: str,
    campaign_goal: str,
    language: str,
    tone: str,
) -> dict[str, Any]:
    """Prepare one deterministic, no-send draft queue for a 3R category."""
    contacts = _contacts_for_category(fixture, marketing_category)
    campaign = _campaign_for_segment(marketing_category, campaign_goal, language, tone)
    drafts: list[dict[str, Any]] = []
    for contact in contacts:
        model_context = build_model_context(campaign, contact)
        model_context.update(
            {
                "marketing_category": marketing_category,
                "language": campaign["language"],
                "tone": campaign["tone"],
            }
        )
        drafts.append(
            {
                "contact_id": contact["id"],
                "review_label": f"{contact['first_name']} {contact['last_name']} · {contact['company']}",
                "model_context": model_context,
                "data_minimisation": build_data_minimisation_record(campaign, contact),
                "status": "queued",
                "no_send": True,
            }
        )
    return {
        "campaign_id": f"{marketing_category}-{uuid.uuid4().hex[:10]}",
        "marketing_category": marketing_category,
        "campaign_goal": campaign["purpose"],
        "language": campaign["language"],
        "tone": campaign["tone"],
        "contact_count": len(drafts),
        "drafts": drafts,
        "approval": {"status": "pending_operator_approval"},
        "delivery_mode": DELIVERY_MODE,
        "no_send": True,
    }


class SegmentDraftRegistry:
    """Persist a locally reviewable, no-send fictional campaign queue."""

    def __init__(self, state_dir: Path):
        self.state_dir = state_dir
        self.state_file = state_dir / "segment-draft-queues.json"
        self.events_file = state_dir / "campaign-events.json"

    def _load(self) -> dict[str, dict[str, Any]]:
        if not self.state_file.exists():
            return {}
        records = json.loads(self.state_file.read_text(encoding="utf-8"))
        if not isinstance(records, dict):
            raise ValueError("invalid local segment draft registry")
        return records

    def _save(self, records: dict[str, dict[str, Any]]) -> None:
        self.state_dir.mkdir(parents=True, exist_ok=True)
        temporary = self.state_file.with_suffix(".tmp")
        temporary.write_text(json.dumps(records, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
        temporary.replace(self.state_file)

    def _append_event(self, record: dict[str, Any], event_type: str) -> None:
        self.state_dir.mkdir(parents=True, exist_ok=True)
        events: list[dict[str, Any]] = []
        if self.events_file.exists():
            events = json.loads(self.events_file.read_text(encoding="utf-8"))
        events.append(
            {
                "event_id": f"evt-{uuid.uuid4().hex[:12]}",
                "campaign_id": record["campaign_id"],
                "marketing_category": record["marketing_category"],
                "event_type": event_type,
                "contact_count": record["contact_count"],
                "delivery_mode": DELIVERY_MODE,
                "no_send": True,
            }
        )
        temporary = self.events_file.with_suffix(".tmp")
        temporary.write_text(json.dumps(events, ensure_ascii=False, indent=2), encoding="utf-8")
        temporary.replace(self.events_file)

    @staticmethod
    def _operator_view(record: dict[str, Any]) -> dict[str, Any]:
        return {
            "approval_id": record["approval_id"],
            "campaign_id": record["campaign_id"],
            "marketing_category": record["marketing_category"],
            "campaign_goal": record["campaign_goal"],
            "language": record["language"],
            "tone": record["tone"],
            "contact_count": record["contact_count"],
            "drafts": record["drafts"],
            "approval": record["approval"],
            "delivery_mode": DELIVERY_MODE,
            "no_send": True,
        }

    def create_preflight(self, preflight: dict[str, Any]) -> dict[str, Any]:
        if not preflight.get("no_send") or preflight.get("delivery_mode") != DELIVERY_MODE:
            raise ValueError("draft-only segment preflight is required")
        approval_id = f"segment-{uuid.uuid4().hex[:12]}"
        record = {
            **preflight,
            "approval_id": approval_id,
            "approval": {
                "status": "pending_operator_approval",
                "required_command": f"/email-approve-segment {approval_id}",
                "required_for": ["draft_queue", "fictional_recipients", "purpose"],
            },
        }
        records = self._load()
        records[approval_id] = record
        self._save(records)
        self._append_event(record, "preflight_created")
        return self._operator_view(record)

    def approve(self, approval_id: str) -> dict[str, Any]:
        records = self._load()
        record = records.get(approval_id)
        if record is None:
            raise ValueError("unknown approval id")
        if record["approval"]["status"] != "pending_operator_approval":
            raise ValueError("approval is no longer pending")
        record["approval"] = {
            **record["approval"],
            "status": "approved_for_batch_generation",
        }
        self._save(records)
        self._append_event(record, "approved_for_batch_generation")
        return self._operator_view(record)

    def claim_for_generation(self, approval_id: str) -> dict[str, Any]:
        records = self._load()
        record = records.get(approval_id)
        if record is None:
            raise ValueError("unknown approval id")
        if record["approval"]["status"] != "approved_for_batch_generation":
            raise ValueError("draft queue generation is not approved")
        record["approval"] = {
            **record["approval"],
            "status": "generation_claimed",
        }
        self._save(records)
        self._append_event(record, "generation_claimed")
        return record

    def record_generated_drafts(self, approval_id: str, generated_drafts: list[str]) -> dict[str, Any]:
        """Store generated fictional drafts for human review; delivery remains impossible."""
        records = self._load()
        record = records.get(approval_id)
        if record is None:
            raise ValueError("unknown approval id")
        if record["approval"]["status"] != "generation_claimed":
            raise ValueError("draft queue generation was not claimed")
        if len(generated_drafts) != record["contact_count"]:
            raise ValueError("generated draft count does not match fictional cohort")
        for item, generated_draft in zip(record["drafts"], generated_drafts, strict=True):
            item["generated_draft"] = generated_draft
            item["status"] = "needs_review"
        record["approval"] = {
            **record["approval"],
            "status": "drafts_ready_for_review",
        }
        self._save(records)
        self._append_event(record, "drafts_created")
        return self._operator_view(record)

    def get_ready_for_review(self, approval_id: str) -> dict[str, Any]:
        records = self._load()
        record = records.get(approval_id)
        if record is None:
            raise ValueError("unknown approval id")
        if record["approval"]["status"] != "drafts_ready_for_review":
            raise ValueError("drafts are not ready for review")
        return self._operator_view(record)

    def replace_review_draft(self, approval_id: str, position: int, draft: str, *, event_type: str) -> dict[str, Any]:
        """Replace one reviewed draft locally; this never creates a delivery path."""
        records = self._load()
        record = records.get(approval_id)
        if record is None:
            raise ValueError("unknown approval id")
        if record["approval"]["status"] != "drafts_ready_for_review":
            raise ValueError("drafts are not ready for review")
        if position < 0 or position >= record["contact_count"]:
            raise ValueError("draft position is outside the fictional cohort")
        if not draft.strip():
            raise ValueError("reviewed draft must not be empty")
        record["drafts"][position]["generated_draft"] = draft.strip()
        record["drafts"][position]["status"] = "needs_review"
        self._save(records)
        self._append_event(record, event_type)
        return self._operator_view(record)

    def get_ready_for_export(self, approval_id: str) -> dict[str, Any]:
        records = self._load()
        record = records.get(approval_id)
        if record is None:
            raise ValueError("unknown approval id")
        if record["approval"]["status"] != "drafts_ready_for_review":
            raise ValueError("drafts are not ready for local export")
        return record

    def record_export(self, approval_id: str, export: dict[str, Any]) -> dict[str, Any]:
        records = self._load()
        record = records.get(approval_id)
        if record is None:
            raise ValueError("unknown approval id")
        if record["approval"]["status"] != "drafts_ready_for_review":
            raise ValueError("drafts are not ready for local export")
        record["export"] = export
        record["approval"] = {
            **record["approval"],
            "status": "exported_for_review",
        }
        self._save(records)
        self._append_event(record, "drafts_exported")
        return self._operator_view(record)
