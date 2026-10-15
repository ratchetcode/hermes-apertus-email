"""Deterministic no-send preparation for fictional Apertus email drafts."""

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any, Callable
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


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


def _model_messages(model_context: dict[str, Any], review_instruction: str | None = None) -> list[dict[str, str]]:
    """Build a closed prompt from the already-minimised model context."""
    user_content = "Create a draft from this approved, fictional context:\n" + json.dumps(model_context, ensure_ascii=False, sort_keys=True)
    if review_instruction:
        user_content += "\n\nRevise the existing fictional draft according to this operator instruction:\n" + review_instruction
    return [
        {
            "role": "system",
            "content": (
                "You draft a concise German invitation email. Return only a subject "
                "line and body text. Use only facts in the supplied JSON. Do not "
                "invent contact details, commitments, prices, links, or claims. "
                "This is a draft only; never send or imply that an email was sent."
            ),
        },
        {
            "role": "user",
            "content": user_content,
        },
    ]


def _post_openai_json(
    url: str,
    headers: dict[str, str],
    payload: dict[str, Any],
    timeout_seconds: int,
) -> dict[str, Any]:
    """Call an OpenAI-compatible endpoint without any email-send capability."""
    request = Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers=headers,
        method="POST",
    )
    try:
        with urlopen(request, timeout=timeout_seconds) as response:
            return json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        raise RuntimeError(f"model endpoint returned HTTP {exc.code}") from exc
    except URLError as exc:
        raise RuntimeError("model endpoint is unavailable") from exc


def _extract_draft(model_response: dict[str, Any]) -> str:
    try:
        content = model_response["choices"][0]["message"]["content"]
    except (IndexError, KeyError, TypeError) as exc:
        raise ValueError("model response contains no draft content") from exc
    if not isinstance(content, str) or not content.strip():
        raise ValueError("model response contains no draft content")
    return content.strip()


def generate_draft(
    preflight: dict[str, Any],
    *,
    model_name: str,
    base_url: str,
    api_key: str,
    post_json: Callable[[str, dict[str, str], dict[str, Any], int], dict[str, Any]] = _post_openai_json,
) -> dict[str, Any]:
    """Generate a draft from the preflight context; this function cannot send email."""
    if not preflight.get("no_send"):
        raise ValueError("no-send preflight is required")

    payload = {
        "model": model_name,
        "messages": _model_messages(
            preflight["model_context"],
            str(preflight.get("review_instruction", "")).strip() or None,
        ),
        "temperature": 0.2,
    }
    response = post_json(
        base_url.rstrip("/") + "/chat/completions",
        {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        payload,
        30,
    )
    return {
        **preflight,
        "draft": _extract_draft(response),
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Prepare a fictional, no-send Apertus draft request."
    )
    parser.add_argument("--contact-id", required=True)
    parser.add_argument("--fixture", type=Path, default=DEFAULT_FIXTURE_PATH)
    parser.add_argument(
        "--live",
        action="store_true",
        help="Generate a draft through the configured Apertus endpoint; never sends email.",
    )
    args = parser.parse_args()

    result = prepare_draft_request(load_fixture(args.fixture), args.contact_id)
    if args.live:
        try:
            result = generate_draft(
                result,
                model_name=os.environ["LLM_NAME"],
                base_url=os.environ["LLM_BASE_URL"],
                api_key=os.environ["LLM_API_KEY"],
            )
        except (RuntimeError, ValueError) as exc:
            result["error"] = {
                "stage": "draft_generation",
                "message": str(exc),
            }
            print(json.dumps(result, ensure_ascii=False, indent=2))
            return 2
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
