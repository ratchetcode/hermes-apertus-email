"""Persistent, no-send approval records for the fictional email-drafting demo."""

from __future__ import annotations

import json
import sys
import uuid
from pathlib import Path
from typing import Any


SRC_DIR = Path(__file__).resolve().parent
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from workflow import prepare_draft_request


ALLOWED_WORKFLOW_TYPES = {"newsletter", "campaign", "follow_up"}


class DraftRegistry:
    """Persist one-time operator approvals outside the model context.

    The registry is intentionally local to the isolated Hermes runtime. It never
    sends mail, updates a CRM, or exposes recipient data to a model payload.
    """

    def __init__(self, state_dir: Path):
        self.state_dir = state_dir
        self.state_file = state_dir / "draft-approvals.json"

    def _load(self) -> dict[str, dict[str, Any]]:
        if not self.state_file.exists():
            return {}
        loaded = json.loads(self.state_file.read_text(encoding="utf-8"))
        if not isinstance(loaded, dict):
            raise ValueError("invalid local draft approval registry")
        return loaded

    def _save(self, records: dict[str, dict[str, Any]]) -> None:
        self.state_dir.mkdir(parents=True, exist_ok=True)
        temporary = self.state_file.with_suffix(".tmp")
        temporary.write_text(
            json.dumps(records, ensure_ascii=False, indent=2, sort_keys=True),
            encoding="utf-8",
        )
        temporary.replace(self.state_file)

    @staticmethod
    def _operator_view(record: dict[str, Any]) -> dict[str, Any]:
        """Return a transparent but minimised record for Hermes and its operator."""
        preflight = record["preflight"]
        return {
            "approval_id": record["approval_id"],
            "workflow_type": record["workflow_type"],
            "parent_draft_id": record.get("parent_draft_id"),
            "model_context": preflight["model_context"],
            "data_minimisation": preflight["data_minimisation"],
            "approval": record["approval"],
            "no_send": True,
        }

    def create_preflight(
        self,
        preflight: dict[str, Any],
        *,
        workflow_type: str,
        parent_draft_id: str | None = None,
    ) -> dict[str, Any]:
        if workflow_type not in ALLOWED_WORKFLOW_TYPES:
            raise ValueError("unsupported workflow type")
        if workflow_type == "follow_up" and not parent_draft_id:
            raise ValueError("follow_up requires a parent draft reference")
        if not preflight.get("no_send"):
            raise ValueError("no-send preflight is required")

        approval_id = f"draft-{uuid.uuid4().hex[:12]}"
        record = {
            "approval_id": approval_id,
            "workflow_type": workflow_type,
            "parent_draft_id": parent_draft_id,
            "preflight": preflight,
            "approval": {
                "status": "pending_operator_approval",
                "required_command": f"/email-approve {approval_id}",
                "required_for": ["draft", "recipient", "purpose"],
            },
        }
        records = self._load()
        records[approval_id] = record
        self._save(records)
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
            "status": "approved_for_one_draft",
        }
        self._save(records)
        return self._operator_view(record)

    def claim_for_generation(self, approval_id: str) -> dict[str, Any]:
        records = self._load()
        record = records.get(approval_id)
        if record is None:
            raise ValueError("unknown approval id")
        if record["approval"]["status"] != "approved_for_one_draft":
            raise ValueError("draft generation is not approved")
        record["approval"] = {
            **record["approval"],
            "status": "generation_claimed",
        }
        self._save(records)
        return record


def create_fictional_preflight(
    fixture: dict[str, Any],
    contact_id: str,
    registry: DraftRegistry,
    *,
    workflow_type: str,
    parent_draft_id: str | None = None,
) -> dict[str, Any]:
    """Build and locally register one safe draft request for the plugin."""
    return registry.create_preflight(
        prepare_draft_request(fixture, contact_id),
        workflow_type=workflow_type,
        parent_draft_id=parent_draft_id,
    )
