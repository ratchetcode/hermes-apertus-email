"""Hermes plugin for the controlled, fictional no-send email draft workflow."""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Any


WORKSPACE = Path(os.environ.get("EMAIL_FRAMEWORK_WORKSPACE", "/workspace"))
SRC_DIR = WORKSPACE / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from email_framework import DraftRegistry, create_fictional_preflight
from contact_review_queue import (
    MARKETING_CATEGORIES,
    ContactReviewRegistry,
    contact_overview,
    contacts_for_category,
    load_demo_contacts,
)
from draft_export import export_segment_drafts
from segment_queue import SegmentDraftRegistry, prepare_segment_preflight
from workflow import generate_draft, load_fixture


TOOLSET = "email_framework"
FIXTURE_PATH = WORKSPACE / "tests" / "fixtures" / "test_contacts.json"
CONTACTS_CSV = WORKSPACE / "data" / "demo_contacts_3r.csv"
STATE_DIR = Path(os.environ.get("HERMES_HOME", "/opt/data")) / "email-framework"
ACTIVE_REVIEW_QUEUE_FILE = STATE_DIR / "active-contact-review-queue.txt"
def _schema(name: str, description: str, properties: dict[str, Any], required: list[str]) -> dict[str, Any]:
    return {
        "name": name,
        "description": description,
        "parameters": {
            "type": "object",
            "properties": properties,
            "required": required,
            "additionalProperties": False,
        },
    }


EMAIL_PREFLIGHT_SCHEMA = _schema(
    "email_framework_preflight",
    "Create a deterministic no-send preflight for one fictional contact. Use this before any draft generation. It returns an approval ID; the operator must type /email-approve <id> before the approved-draft tool can run.",
    {
        "contact_id": {
            "type": "string",
            "enum": ["demo-contact-001", "demo-contact-002"],
            "description": "Fictional contact identifier only.",
        },
        "workflow_type": {
            "type": "string",
            "enum": ["newsletter", "campaign", "follow_up"],
            "description": "Draft classification. follow_up requires parent_draft_id.",
        },
        "parent_draft_id": {
            "type": "string",
            "description": "Required local draft reference for a follow-up; never a recipient ID or CRM ID.",
        },
    },
    ["contact_id", "workflow_type"],
)

EMAIL_GENERATE_SCHEMA = _schema(
    "email_framework_generate_approved_draft",
    "Generate exactly one no-send draft from an operator-approved fictional preflight. The approval ID must first be approved by the operator with /email-approve <id>. Never call this tool before that slash-command approval.",
    {
        "approval_id": {
            "type": "string",
            "description": "Approval ID returned by email_framework_preflight and explicitly approved by the operator.",
        }
    },
    ["approval_id"],
)


EMAIL_SEGMENT_PREFLIGHT_SCHEMA = _schema(
    "email_framework_segment_preflight",
    "Create a deterministic no-send preflight for one fictional 3R cohort of eight contacts. Use this before generating any personalised batch drafts. The operator must later type /email-approve-segment <id>.",
    {
        "marketing_category": {
            "type": "string",
            "enum": ["recruit", "retain", "recover"],
            "description": "Fictional lifecycle category; every selected cohort has exactly eight demo contacts.",
        },
        "campaign_goal": {"type": "string", "description": "Fictional campaign goal."},
        "language": {"type": "string", "description": "Draft language, for example de."},
        "tone": {"type": "string", "description": "Writing tone, for example freundlich und sachlich."},
    },
    ["marketing_category", "campaign_goal", "language", "tone"],
)

EMAIL_SEGMENT_GENERATE_SCHEMA = _schema(
    "email_framework_generate_segment_drafts",
    "Generate exactly eight personalised, fictional no-send drafts from a previously approved 3R cohort preflight. Never call this before /email-approve-segment <id>; it has no delivery capability.",
    {
        "approval_id": {
            "type": "string",
            "description": "Segment approval ID returned by email_framework_segment_preflight and explicitly approved by the operator.",
        }
    },
    ["approval_id"],
)


def _registry() -> DraftRegistry:
    return DraftRegistry(STATE_DIR)


def _segment_registry() -> SegmentDraftRegistry:
    return SegmentDraftRegistry(STATE_DIR)


def _contact_review_registry() -> ContactReviewRegistry:
    return ContactReviewRegistry(STATE_DIR)


def _active_review_queue_id() -> str:
    if not ACTIVE_REVIEW_QUEUE_FILE.exists():
        raise ValueError("no active contact review queue")
    queue_id = ACTIVE_REVIEW_QUEUE_FILE.read_text(encoding="utf-8").strip()
    if not queue_id:
        raise ValueError("no active contact review queue")
    return queue_id


def _set_active_review_queue(queue_id: str) -> None:
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    temporary = ACTIVE_REVIEW_QUEUE_FILE.with_suffix(".tmp")
    temporary.write_text(queue_id, encoding="utf-8")
    temporary.replace(ACTIVE_REVIEW_QUEUE_FILE)


def _review_status(status: str) -> str:
    return {
        "not_created": "noch nicht erstellt",
        "needs_review": "zur Prüfung",
        "confirmed": "bestätigt",
        "skipped": "übersprungen",
    }.get(status, status)


def _review_view(record: dict[str, Any], *, heading: str | None = None) -> str:
    current = record["current"]
    contact = current["contact"]
    lines = []
    if heading:
        lines.append(heading)
    lines.extend(
        [
            f"Entwurf {current['position']} von {current['total']} – {record['marketing_category']}",
            f"Fiktiver Kontakt: {contact['first_name']} {contact['last_name']} · {contact['company']}",
            f"Interesse: {contact['interest']}",
            f"Ziel: {record['campaign_goal']}",
            f"Status: {_review_status(current['status'])}",
        ]
    )
    if current.get("draft"):
        lines.extend(["", "Aktueller Entwurf:", str(current["draft"])])
    lines.extend(
        [
            "",
            "Nächste Schritte: Weiter, Zurück, Entwurf speichern, Bestätigen, Überspringen oder Abbrechen.",
            "Kein Versand. Es wird nur lokal als Entwurf geprüft.",
        ]
    )
    return "\n".join(lines)


def _demo_contacts(raw_args: str) -> str:
    try:
        contacts = load_demo_contacts(CONTACTS_CSV)
        category = raw_args.strip().lower()
        if not category:
            counts = contact_overview(contacts)
            return (
                "Fiktive Demo-Kontakte:\n"
                f"- recruit: {counts['recruit']}\n"
                f"- retain: {counts['retain']}\n"
                f"- recover: {counts['recover']}\n\n"
                "Für eine Gruppe kann 'recruit', 'retain' oder 'recover' angegeben werden."
            )
        selected = contacts_for_category(contacts, category)
        lines = [f"Fiktive Kontakte – {category}: {len(selected)}"]
        lines.extend(
            f"{index}. {contact['contact_id']} – {contact['first_name']} {contact['last_name']} · {contact['interest']}"
            for index, contact in enumerate(selected, start=1)
        )
        return "\n".join(lines)
    except ValueError as exc:
        return f"Kontaktansicht nicht verfügbar: {exc}."


def _demo_review_start(raw_args: str) -> str:
    try:
        category, separator, campaign_goal = raw_args.partition("|")
        if not separator:
            raise ValueError("Format: <recruit|retain|recover> | <Ziel der Nachricht>")
        category = category.strip().lower()
        if category not in MARKETING_CATEGORIES:
            raise ValueError("Kategorie muss recruit, retain oder recover sein")
        record = _contact_review_registry().create_queue(
            load_demo_contacts(CONTACTS_CSV),
            marketing_category=category,
            campaign_goal=campaign_goal,
        )
        _set_active_review_queue(record["queue_id"])
        return _review_view(record, heading="Kontaktbezogene Entwurfsprüfung gestartet.")
    except ValueError as exc:
        return f"Entwurfsprüfung nicht gestartet: {exc}."


def _demo_review_current(_raw_args: str) -> str:
    try:
        return _review_view(_contact_review_registry().current(_active_review_queue_id()))
    except ValueError as exc:
        return f"Entwurfsprüfung nicht verfügbar: {exc}."


def _demo_review_next(_raw_args: str) -> str:
    try:
        return _review_view(_contact_review_registry().next(_active_review_queue_id()))
    except ValueError as exc:
        return f"Weiter nicht möglich: {exc}."


def _demo_review_previous(_raw_args: str) -> str:
    try:
        return _review_view(_contact_review_registry().previous(_active_review_queue_id()))
    except ValueError as exc:
        return f"Zurück nicht möglich: {exc}."


def _demo_review_draft(raw_args: str) -> str:
    try:
        draft = raw_args.strip()
        if not draft:
            raise ValueError("ein Entwurfstext ist erforderlich")
        return _review_view(_contact_review_registry().replace_draft(_active_review_queue_id(), draft))
    except ValueError as exc:
        return f"Entwurf nicht gespeichert: {exc}."


def _demo_review_confirm(_raw_args: str) -> str:
    try:
        return _review_view(_contact_review_registry().confirm_current(_active_review_queue_id()))
    except ValueError as exc:
        return f"Bestätigung nicht möglich: {exc}."


def _demo_review_skip(_raw_args: str) -> str:
    try:
        return _review_view(_contact_review_registry().skip_current(_active_review_queue_id()))
    except ValueError as exc:
        return f"Überspringen nicht möglich: {exc}."


def _demo_review_abort(_raw_args: str) -> str:
    try:
        return _review_view(_contact_review_registry().abort(_active_review_queue_id()), heading="Entwurfsprüfung abgebrochen.")
    except ValueError as exc:
        return f"Abbruch nicht möglich: {exc}."


def _json(value: dict[str, Any]) -> str:
    return json.dumps(value, ensure_ascii=False, indent=2)


def _preflight(args: dict[str, Any]) -> str:
    try:
        workflow_type = args["workflow_type"]
        record = create_fictional_preflight(
            load_fixture(FIXTURE_PATH),
            args["contact_id"],
            _registry(),
            workflow_type=workflow_type,
            parent_draft_id=args.get("parent_draft_id"),
        )
        return _json(
            {
                "success": True,
                **record,
                "next_step": (
                    f"Ask the operator to type {record['approval']['required_command']}. "
                    "Do not generate a draft before that exact slash-command approval."
                ),
            }
        )
    except (KeyError, ValueError) as exc:
        return _json({"success": False, "stage": "preflight", "error": str(exc), "no_send": True})


def _segment_preflight(args: dict[str, Any]) -> str:
    try:
        preflight = prepare_segment_preflight(
            load_fixture(FIXTURE_PATH),
            marketing_category=args["marketing_category"],
            campaign_goal=args["campaign_goal"],
            language=args["language"],
            tone=args["tone"],
        )
        record = _segment_registry().create_preflight(preflight)
        return _json(
            {
                "success": True,
                **record,
                "next_step": (
                    f"Review the eight fictional, minimised contexts and ask the operator to type "
                    f"{record['approval']['required_command']}. Do not generate drafts before that command."
                ),
            }
        )
    except (KeyError, ValueError) as exc:
        return _json({"success": False, "stage": "segment_preflight", "error": str(exc), "no_send": True})


def _segment_preflight_command(raw_args: str) -> str:
    """Run the deterministic 3R preflight without relying on model tool syntax."""
    try:
        args = json.loads(raw_args)
        if not isinstance(args, dict):
            raise ValueError("segment preflight arguments must be a JSON object")
    except (json.JSONDecodeError, ValueError) as exc:
        return _json({"success": False, "stage": "segment_preflight", "error": str(exc), "no_send": True})
    return _segment_preflight(args)


def _generate_approved_draft(args: dict[str, Any]) -> str:
    try:
        record = _registry().claim_for_generation(args["approval_id"])
        result = generate_draft(
            record["preflight"],
            model_name=os.environ["LLM_NAME"],
            base_url=os.environ["LLM_BASE_URL"],
            api_key=os.environ["LLM_API_KEY"],
        )
        return _json(
            {
                "success": True,
                "approval_id": record["approval_id"],
                "workflow_type": record["workflow_type"],
                "model_context": result["model_context"],
                "data_minimisation": result["data_minimisation"],
                "approval": result["approval"],
                "draft": result["draft"],
                "no_send": True,
            }
        )
    except (KeyError, RuntimeError, ValueError) as exc:
        return _json(
            {
                "success": False,
                "stage": "draft_generation",
                "error": str(exc),
                "no_send": True,
            }
        )


def _generate_segment_drafts(args: dict[str, Any]) -> str:
    try:
        record = _segment_registry().claim_for_generation(args["approval_id"])
        generated = [
            generate_draft(
                {
                    "model_context": item["model_context"],
                    "data_minimisation": item["data_minimisation"],
                    "no_send": True,
                },
                model_name=os.environ["LLM_NAME"],
                base_url=os.environ["LLM_BASE_URL"],
                api_key=os.environ["LLM_API_KEY"],
            )["draft"]
            for item in record["drafts"]
        ]
        result = _segment_registry().record_generated_drafts(record["approval_id"], generated)
        return _json(
            {
                "success": True,
                **result,
                "next_step": "Review each of the eight drafts. They remain fictional, draft-only and have no delivery path.",
            }
        )
    except (KeyError, RuntimeError, ValueError) as exc:
        return _json(
            {
                "success": False,
                "stage": "segment_draft_generation",
                "error": str(exc),
                "no_send": True,
            }
        )


def _generate_segment_command(raw_args: str) -> str:
    """Generate approved fictional cohort drafts through an explicit command."""
    approval_id = raw_args.strip()
    if not approval_id:
        return _json(
            {
                "success": False,
                "stage": "segment_draft_generation",
                "error": "missing approval ID",
                "no_send": True,
            }
        )
    return _generate_segment_drafts({"approval_id": approval_id})


def _export_segment_command(raw_args: str) -> str:
    """Write ready fictional cohort drafts as local importable .eml files only."""
    approval_id = raw_args.strip()
    if not approval_id:
        return _json(
            {
                "success": False,
                "stage": "draft_export",
                "error": "missing approval ID",
                "no_send": True,
            }
        )
    try:
        registry = _segment_registry()
        record = registry.get_ready_for_export(approval_id)
        export = export_segment_drafts(
            record,
            load_fixture(FIXTURE_PATH),
            STATE_DIR / "exports",
        )
        registry.record_export(approval_id, export)
        return _json({"success": True, **export})
    except (KeyError, RuntimeError, ValueError) as exc:
        return _json(
            {
                "success": False,
                "stage": "draft_export",
                "error": str(exc),
                "no_send": True,
            }
        )


def _approve(raw_args: str) -> str:
    approval_id = raw_args.strip()
    if not approval_id:
        return "Usage: /email-approve <approval-id>"
    try:
        record = _registry().approve(approval_id)
        return _json(
            {
                "success": True,
                "approval_id": record["approval_id"],
                "approval": record["approval"],
                "no_send": True,
                "next_step": "Hermes may now generate exactly one draft using the approved-draft tool.",
            }
        )
    except ValueError as exc:
        return _json({"success": False, "error": str(exc), "no_send": True})


def _approve_segment(raw_args: str) -> str:
    approval_id = raw_args.strip()
    if not approval_id:
        return "Usage: /email-approve-segment <approval-id>"
    try:
        record = _segment_registry().approve(approval_id)
        return _json(
            {
                "success": True,
                "approval_id": record["approval_id"],
                "approval": record["approval"],
                "contact_count": record["contact_count"],
                "delivery_mode": "draft_only",
                "no_send": True,
                "next_step": "Hermes may now generate eight personalised, fictional drafts using the segment-draft tool.",
            }
        )
    except ValueError as exc:
        return _json({"success": False, "error": str(exc), "no_send": True})


def _status(_raw_args: str) -> str:
    return (
        "Apertus Email Framework (fictional, no-send):\n"
        "1. Ask Hermes for one draft or a 3R cohort campaign (Recruit, Retain, Recover).\n"
        "2. Hermes must call a deterministic no-send preflight first.\n"
        "3. Review used/excluded fields and type the matching /email-approve command.\n"
        "4. Hermes may generate one draft or eight fictional cohort drafts; no email is ever sent."
    )


def register(ctx) -> None:
    ctx.register_tool(
        name="email_framework_preflight",
        toolset=TOOLSET,
        schema=EMAIL_PREFLIGHT_SCHEMA,
        handler=_preflight,
        emoji="🛡️",
    )
    ctx.register_tool(
        name="email_framework_generate_approved_draft",
        toolset=TOOLSET,
        schema=EMAIL_GENERATE_SCHEMA,
        handler=_generate_approved_draft,
        emoji="✉️",
    )
    ctx.register_tool(
        name="email_framework_segment_preflight",
        toolset=TOOLSET,
        schema=EMAIL_SEGMENT_PREFLIGHT_SCHEMA,
        handler=_segment_preflight,
        emoji="🛡️",
    )
    ctx.register_tool(
        name="email_framework_generate_segment_drafts",
        toolset=TOOLSET,
        schema=EMAIL_SEGMENT_GENERATE_SCHEMA,
        handler=_generate_segment_drafts,
        emoji="✉️",
    )
    ctx.register_command(
        "email-approve",
        handler=_approve,
        description="Approve exactly one fictional, no-send email draft preflight.",
        args_hint="<approval-id>",
    )
    ctx.register_command(
        "email-approve-segment",
        handler=_approve_segment,
        description="Approve one fictional 3R cohort for eight no-send drafts.",
        args_hint="<approval-id>",
    )
    ctx.register_command(
        "email-preflight-segment",
        handler=_segment_preflight_command,
        description="Create a deterministic no-send preflight for one fictional 3R cohort.",
        args_hint="<JSON arguments>",
    )
    ctx.register_command(
        "email-generate-segment",
        handler=_generate_segment_command,
        description="Generate eight fictional draft-only emails after explicit segment approval.",
        args_hint="<approval-id>",
    )
    ctx.register_command(
        "email-export-segment",
        handler=_export_segment_command,
        description="Export eight ready fictional drafts as local .eml files for review.",
        args_hint="<approval-id>",
    )
    ctx.register_command(
        "email-framework",
        handler=_status,
        description="Show the controlled newsletter and follow-up draft workflow.",
    )
    ctx.register_command(
        "email-demo-contacts",
        handler=_demo_contacts,
        description="Show fictional demo contacts by 3R category without addresses.",
        args_hint="[recruit|retain|recover]",
    )
    ctx.register_command(
        "email-demo-review-start",
        handler=_demo_review_start,
        description="Start a local no-send per-contact review queue for one fictional 3R group.",
        args_hint="<category> | <campaign goal>",
    )
    ctx.register_command(
        "email-demo-review-current",
        handler=_demo_review_current,
        description="Show the current fictional contact and draft in the local review queue.",
    )
    ctx.register_command(
        "email-demo-review-next",
        handler=_demo_review_next,
        description="Move to the next fictional contact in the local review queue.",
    )
    ctx.register_command(
        "email-demo-review-previous",
        handler=_demo_review_previous,
        description="Move to the previous fictional contact in the local review queue.",
    )
    ctx.register_command(
        "email-demo-review-draft",
        handler=_demo_review_draft,
        description="Store the current fictional contact's draft locally for review.",
        args_hint="<draft text>",
    )
    ctx.register_command(
        "email-demo-review-confirm",
        handler=_demo_review_confirm,
        description="Confirm the current local fictional draft; this never sends email.",
    )
    ctx.register_command(
        "email-demo-review-skip",
        handler=_demo_review_skip,
        description="Skip the current fictional contact in the local review queue.",
    )
    ctx.register_command(
        "email-demo-review-abort",
        handler=_demo_review_abort,
        description="Abort the active local fictional review queue.",
    )
