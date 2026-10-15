"""Local, draft-only RFC 5322 export for the fictional campaign demonstrator."""

from __future__ import annotations

import hashlib
import json
import shutil
import tempfile
from datetime import UTC, datetime
from email.message import EmailMessage
from email.policy import SMTP
from pathlib import Path
from typing import Any


DEMO_FROM = "Apertus Draft Gate <drafts@example.invalid>"


def _subject_and_body(draft: str) -> tuple[str, str]:
    lines = draft.strip().splitlines()
    if not lines:
        raise ValueError("generated draft is empty")
    first_line = lines[0]
    for prefix in ("Betreff:", "Subject:"):
        if first_line.lower().startswith(prefix.lower()):
            subject = first_line[len(prefix) :].strip()
            if not subject:
                raise ValueError("generated draft has no subject")
            body = "\n".join(lines[1:]).lstrip()
            if not body:
                raise ValueError("generated draft has no body")
            return subject, body
    raise ValueError("generated draft must start with Betreff: or Subject:")


def _contact_index(fixture: dict[str, Any]) -> dict[str, dict[str, Any]]:
    contacts = fixture.get("contacts")
    if not isinstance(contacts, list):
        raise ValueError("fictional contact fixture is invalid")
    return {str(contact["id"]): contact for contact in contacts}


def export_segment_drafts(
    record: dict[str, Any],
    fixture: dict[str, Any],
    export_root: Path,
) -> dict[str, Any]:
    """Write reviewed fictional drafts as local .eml files and a manifest only."""
    if record.get("delivery_mode") != "draft_only" or not record.get("no_send"):
        raise ValueError("draft-only campaign record is required")
    if record.get("approval", {}).get("status") != "drafts_ready_for_review":
        raise ValueError("drafts are not ready for local export")

    approval_id = str(record["approval_id"])
    contacts = _contact_index(fixture)
    export_root.mkdir(parents=True, exist_ok=True)
    target_dir = export_root / approval_id
    if target_dir.exists():
        raise ValueError("draft export already exists for this approval")
    temporary_dir = Path(tempfile.mkdtemp(prefix=f".{approval_id}-", dir=export_root))

    try:
        manifest_drafts: list[dict[str, str]] = []
        for position, item in enumerate(record["drafts"], start=1):
            contact = contacts.get(str(item["contact_id"]))
            if contact is None:
                raise ValueError("draft references an unknown fictional contact")
            recipient = str(contact.get("email", ""))
            if not recipient.endswith("@example.invalid"):
                raise ValueError("local demo export accepts fictional example.invalid recipients only")
            subject, body = _subject_and_body(str(item.get("generated_draft", "")))
            message = EmailMessage(policy=SMTP)
            message["From"] = DEMO_FROM
            message["To"] = recipient
            message["Subject"] = subject
            message["X-Draft-Only"] = "true"
            message["X-Draft-Gate-Approval"] = approval_id
            message["X-Draft-Gate-Contact"] = str(item["contact_id"])
            message.set_content(body)
            filename = f"{position:02d}-{item['contact_id']}.eml"
            output_path = temporary_dir / filename
            raw_message = message.as_bytes()
            output_path.write_bytes(raw_message)
            manifest_drafts.append(
                {
                    "contact_id": str(item["contact_id"]),
                    "file": filename,
                    "sha256": hashlib.sha256(raw_message).hexdigest(),
                    "status": "needs_review",
                }
            )

        manifest = {
            "approval_id": approval_id,
            "campaign_id": record["campaign_id"],
            "status": "needs_review",
            "delivery_mode": "draft_only",
            "no_send": True,
            "created_at": datetime.now(UTC).isoformat(),
            "drafts": manifest_drafts,
        }
        (temporary_dir / "manifest.json").write_text(
            json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True),
            encoding="utf-8",
        )
        temporary_dir.replace(target_dir)
        return {
            "approval_id": approval_id,
            "export_dir": str(target_dir),
            "manifest": str(target_dir / "manifest.json"),
            "draft_count": len(manifest_drafts),
            "delivery_mode": "draft_only",
            "no_send": True,
        }
    except Exception:
        shutil.rmtree(temporary_dir, ignore_errors=True)
        raise
