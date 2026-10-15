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
from draft_export import export_segment_drafts
from conversation_state import ConversationStateMachine
from segment_queue import SegmentDraftRegistry, prepare_segment_preflight
from workflow import generate_draft, load_fixture


TOOLSET = "email_framework"
FIXTURE_PATH = WORKSPACE / "data" / "test_contacts.json"
STATE_DIR = Path(os.environ.get("HERMES_HOME", "/opt/data")) / "email-framework"
_CONVERSATION_FLOW = ConversationStateMachine()
_CONVERSATION_REPLIES: dict[str, str] = {}


def _conversation_pre_llm_call(*, user_message: str, session_id: str, **_kwargs: Any) -> str:
    """Provide the same deterministic workflow for the local TUI surface."""
    handled = _conversation_admission(text=user_message, session_key=session_id)
    _CONVERSATION_REPLIES[session_id] = handled["reply"]
    return "The controlled workflow owns the operator response. Do not add visible text."


def _conversation_transform_llm_output(*, response_text: str, session_id: str, **_kwargs: Any) -> str:
    return _CONVERSATION_REPLIES.pop(session_id, response_text)


def _conversation_admission(*, text: str, session_key: str, **_kwargs: Any) -> dict[str, str]:
    """Exclusively handle the controlled workflow before an agent turn is created."""
    result = _CONVERSATION_FLOW.advance(session_key, text)
    reply = result["reply"]
    action = result["action"]
    if action and action["kind"] == "segment_preflight":
        preflight = json.loads(_segment_preflight(action["arguments"]))
        if preflight.get("success"):
            _CONVERSATION_FLOW.bind_approval(session_key, preflight["approval_id"])
            reply = (
                f"Controlled preflight created: {preflight['contact_count']} fictional contacts; no email will be sent. "
                "Would you like to create the eight drafts now? [Yes / No]"
                if action["arguments"]["language"] == "English"
                else f"Kontrollierter Preflight erstellt: {preflight['contact_count']} fiktive Kontakte, kein Versand. Möchten Sie die acht Entwürfe jetzt erstellen? [Ja / Nein]"
            )
        else:
            reply = f"Preflight failed safely: {preflight['error']}"
    elif action and action["kind"] == "approve_and_generate":
        approval_id = action["arguments"]["approval_id"]
        approved = json.loads(_approve_segment(approval_id))
        generated = json.loads(_generate_segment_command(approval_id)) if approved.get("success") else approved
        if generated.get("success"):
            _CONVERSATION_FLOW.mark_drafts_ready(session_key)
            reply = "Eight fictional drafts were created for review. Would you like to save them as local .eml files now? [Yes / No]"
        else:
            reply = f"Draft generation stopped safely: {generated.get('error', 'unknown error')}"
    elif action and action["kind"] == "export":
        exported = json.loads(_export_segment_command(action["arguments"]["approval_id"]))
        reply = (
            f"Eight draft files and manifest.json were saved for review in: {exported['export_dir']}"
            if exported.get("success")
            else f"Draft export stopped safely: {exported.get('error', 'unknown error')}"
        )
    return {"action": "handled", "reply": reply}


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
    ctx.register_hook("post_gateway_admission", _conversation_admission)
    ctx.register_hook("pre_llm_call", _conversation_pre_llm_call)
    ctx.register_hook("transform_llm_output", _conversation_transform_llm_output)
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
