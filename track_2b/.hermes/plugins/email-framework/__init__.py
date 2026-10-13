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
from workflow import generate_draft, load_fixture


TOOLSET = "email_framework"
FIXTURE_PATH = WORKSPACE / "data" / "test_contacts.json"
STATE_DIR = Path(os.environ.get("HERMES_HOME", "/opt/data")) / "email-framework"


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


def _registry() -> DraftRegistry:
    return DraftRegistry(STATE_DIR)


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


def _status(_raw_args: str) -> str:
    return (
        "Apertus Email Framework (fictional, no-send):\n"
        "1. Ask Hermes for a newsletter, campaign or follow-up draft.\n"
        "2. Hermes must call the deterministic preflight first.\n"
        "3. Review used/excluded fields and type /email-approve <approval-id>.\n"
        "4. Hermes may generate exactly one draft; no email is ever sent."
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
    ctx.register_command(
        "email-approve",
        handler=_approve,
        description="Approve exactly one fictional, no-send email draft preflight.",
        args_hint="<approval-id>",
    )
    ctx.register_command(
        "email-framework",
        handler=_status,
        description="Show the controlled newsletter and follow-up draft workflow.",
    )
