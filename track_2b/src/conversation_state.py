"""Deterministic text-only operator conversation flow for the fictional 3R demo."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


LANGUAGES = {"de": "Deutsch", "deutsch": "Deutsch", "en": "English", "english": "English", "fr": "Français", "français": "Français", "francais": "Français"}
CATEGORIES = {"recruit", "retain", "recover"}


@dataclass
class _Session:
    state: str = "language"
    values: dict[str, str] = field(default_factory=dict)


class ConversationStateMachine:
    """Stores minimal state in memory; callers persist it only if a verified hook needs it."""

    def __init__(self) -> None:
        self._sessions: dict[str, _Session] = {}

    def _session(self, session_id: str) -> _Session:
        return self._sessions.setdefault(session_id, _Session())

    @staticmethod
    def _reply(language: str, german: str, english: str, french: str) -> str:
        return {"Deutsch": german, "English": english, "Français": french}[language]

    def advance(self, session_id: str, raw_text: str) -> dict[str, Any]:
        session = self._session(session_id)
        text = raw_text.strip()
        normalised = " ".join(text.casefold().split())
        compact = normalised.replace(" ", "")
        if session.state == "language":
            language = LANGUAGES.get(normalised)
            if language is None:
                return {"state": "language", "reply": "Welche Sprache möchten Sie verwenden? [Deutsch / English / Français]", "action": None}
            session.values["language"] = language
            session.state = "workflow"
            return {"state": "workflow", "reply": self._reply(language, "Was möchten Sie vorbereiten? [Einzelkontakt / 3R-Kampagne]", "What would you like to prepare? [Single contact / 3R campaign]", "Que souhaitez-vous préparer ? [Contact individuel / Campagne 3R]"), "action": None}
        language = session.values["language"]
        if session.state == "workflow":
            if compact in {"3r", "3r-kampagne", "kampagne", "campaign", "campagne"}:
                session.state = "category"
                return {"state": "category", "reply": self._reply(language, "Welche 3R-Kategorie? [recruit / retain / recover]", "Which 3R category? [recruit / retain / recover]", "Quelle catégorie 3R ? [recruit / retain / recover]"), "action": None}
            return {"state": "workflow", "reply": self._reply(language, "Bitte wählen Sie Einzelkontakt oder 3R-Kampagne.", "Please choose single contact or 3R campaign.", "Veuillez choisir contact individuel ou campagne 3R."), "action": None}
        if session.state == "category":
            if normalised not in CATEGORIES:
                return {"state": "category", "reply": self._reply(language, "Bitte wählen Sie recruit, retain oder recover.", "Please choose recruit, retain, or recover.", "Veuillez choisir recruit, retain ou recover."), "action": None}
            session.values["marketing_category"] = normalised
            session.state = "goal"
            return {"state": "goal", "reply": self._reply(language, "Wie lautet das Kampagnenziel?", "What is the campaign goal?", "Quel est l’objectif de la campagne ?"), "action": None}
        if session.state == "goal":
            if not text or normalised in {"ja", "nein", "yes", "no", "oui", "non"}:
                return {"state": "goal", "reply": self._reply(language, "Bitte geben Sie ein konkretes Kampagnenziel ein.", "Please provide a concrete campaign goal.", "Veuillez fournir un objectif de campagne concret."), "action": None}
            session.values["campaign_goal"] = text
            session.state = "tone"
            return {"state": "tone", "reply": self._reply(language, "Welchen Ton soll der Entwurf haben?", "What tone should the draft use?", "Quel ton doit avoir le brouillon ?"), "action": None}
        if session.state == "tone":
            if not text:
                return {"state": "tone", "reply": self._reply(language, "Bitte geben Sie den gewünschten Ton ein.", "Please provide the desired tone.", "Veuillez indiquer le ton souhaité."), "action": None}
            session.values["tone"] = text
            session.state = "approval"
            return {"state": "approval", "reply": self._reply(language, "Der kontrollierte Preflight ist bereit.", "The controlled preflight is ready.", "Le précontrôle est prêt."), "action": {"kind": "segment_preflight", "arguments": dict(session.values)}}
        if session.state == "approval":
            if normalised in {"ja", "yes", "oui"}:
                session.state = "generation"
                return {"state": "generation", "reply": self._reply(language, "Die acht fiktiven Entwürfe werden jetzt vorbereitet.", "The eight fictional drafts are now being prepared.", "Les huit brouillons fictifs sont en cours de préparation."), "action": {"kind": "approve_and_generate", "arguments": {"approval_id": session.values["approval_id"]}}}
            if normalised in {"nein", "no", "non"}:
                return {"state": "approval", "reply": self._reply(language, "Keine Entwürfe wurden erzeugt. Der Preflight bleibt zur Prüfung erhalten.", "No drafts were generated. The preflight remains available for review.", "Aucun brouillon n’a été généré. Le précontrôle reste disponible pour examen."), "action": None}
            return {"state": "approval", "reply": self._reply(language, "Möchten Sie die acht fiktiven Entwürfe jetzt erstellen? [Ja / Nein]", "Would you like to create the eight fictional drafts now? [Yes / No]", "Souhaitez-vous créer les huit brouillons fictifs maintenant ? [Oui / Non]"), "action": None}
        if session.state == "export":
            if normalised in {"ja", "yes", "oui"}:
                session.state = "completed"
                return {"state": "completed", "reply": self._reply(language, "Die lokalen Entwurfsdateien werden jetzt gespeichert.", "The local draft files are now being saved.", "Les fichiers de brouillon locaux sont maintenant enregistrés."), "action": {"kind": "export", "arguments": {"approval_id": session.values["approval_id"]}}}
            return {"state": "export", "reply": self._reply(language, "Möchten Sie die acht Entwürfe jetzt als lokale .eml-Dateien speichern? [Ja / Nein]", "Would you like to save the eight drafts as local .eml files now? [Yes / No]", "Souhaitez-vous enregistrer les huit brouillons comme fichiers .eml locaux ? [Oui / Non]"), "action": None}
        return {"state": session.state, "reply": self._reply(language, "Der Vorgang wartet auf die explizite Freigabe.", "The workflow is waiting for explicit approval.", "Le processus attend une approbation explicite."), "action": None}

    def bind_approval(self, session_id: str, approval_id: str) -> None:
        session = self._session(session_id)
        if session.state != "approval":
            raise ValueError("approval can only be bound after preflight")
        session.values["approval_id"] = approval_id

    def mark_drafts_ready(self, session_id: str) -> None:
        session = self._session(session_id)
        if session.state != "generation":
            raise ValueError("drafts can only become ready after explicit approval")
        session.state = "export"
