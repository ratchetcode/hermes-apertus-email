"""Deterministic terminal operator surface for the fictional 3R no-send demo."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Callable

from draft_export import export_segment_drafts
from segment_queue import MARKETING_CATEGORIES, SegmentDraftRegistry, prepare_segment_preflight


YES = {"ja", "j", "yes", "y", "oui", "o"}
LANGUAGES = {"deutsch": "Deutsch", "de": "Deutsch", "english": "English", "en": "English", "français": "Français", "francais": "Français", "fr": "Français"}


def _ask(input_fn: Callable[[str], str], output_fn: Callable[[str], None], prompt: str, allowed: set[str] | None = None) -> str:
    while True:
        value = input_fn(prompt).strip()
        normalised = " ".join(value.casefold().split())
        if allowed is None and value:
            return value
        if allowed is not None and normalised in allowed:
            return normalised
        output_fn(prompt)


def run_console(*, input_fn: Callable[[str], str], output_fn: Callable[[str], None], fixture: dict[str, Any], state_dir: Path, generate_fn: Callable[[dict[str, Any]], dict[str, Any]]) -> dict[str, Any]:
    """Run one bounded workflow. There is no send, approval, or shipping branch."""
    raw_language = _ask(input_fn, output_fn, "Welche Sprache möchten Sie verwenden? [Deutsch / English / Français]", set(LANGUAGES))
    language = LANGUAGES[raw_language]
    if language != "Deutsch":
        output_fn("This deterministic demonstration currently continues in German after language selection.")
    workflow = _ask(input_fn, output_fn, "Was möchten Sie vorbereiten? [3R-Kampagne]", {"3r", "3 r", "3r-kampagne"})
    del workflow
    category = _ask(input_fn, output_fn, "Welche 3R-Kategorie? [recruit / retain / recover]", set(MARKETING_CATEGORIES))
    goal = _ask(input_fn, output_fn, "Wie lautet das Kampagnenziel?")
    tone = _ask(input_fn, output_fn, "Welchen Ton soll der Entwurf haben?")
    preflight = prepare_segment_preflight(fixture, marketing_category=category, campaign_goal=goal, language=language, tone=tone)
    registry = SegmentDraftRegistry(state_dir)
    view = registry.create_preflight(preflight)
    output_fn(f"Ausgewählte fiktive Kontakte ({view['contact_count']}): " + "; ".join(item["review_label"] for item in view["drafts"]))
    if _ask(input_fn, output_fn, "Kontrollierter Preflight erstellt, kein E-Mail-Versand. Acht Entwürfe erstellen? [Ja / Nein]", {"ja", "nein", "yes", "no"}) not in YES:
        return {"exported": False, "draft_count": 0}
    registry.approve(view["approval_id"])
    claimed = registry.claim_for_generation(view["approval_id"])
    drafts = [generate_fn({"model_context": item["model_context"], "no_send": True})["draft"] for item in claimed["drafts"]]
    ready = registry.record_generated_drafts(view["approval_id"], drafts)
    output_fn("Acht fiktive Entwürfe wurden erstellt und warten auf Prüfung.")
    if _ask(input_fn, output_fn, "Als lokale .eml-Dateien speichern? [Ja / Nein]", {"ja", "nein", "yes", "no"}) not in YES:
        return {"exported": False, "draft_count": len(ready["drafts"])}
    record = registry.get_ready_for_export(view["approval_id"])
    exported = export_segment_drafts(record, fixture, state_dir / "exports")
    registry.record_export(view["approval_id"], exported)
    output_fn(f"Acht Entwürfe und manifest.json gespeichert: {exported['export_dir']}")
    return {"exported": True, **exported}
