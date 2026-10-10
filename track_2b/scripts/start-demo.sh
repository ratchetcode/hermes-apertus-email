#!/bin/sh
set -eu

: "${LLM_NAME:?LLM_NAME must be set in .env}"
: "${LLM_BASE_URL:?LLM_BASE_URL must be set in .env}"
: "${LLM_API_KEY:?LLM_API_KEY must be set in .env}"

hermes config set model.default "$LLM_NAME" >/dev/null
hermes config set model.provider custom >/dev/null
hermes config set model.base_url "$LLM_BASE_URL" >/dev/null
hermes config set model.api_key '${LLM_API_KEY}' >/dev/null

cat <<'EOF'

Hermes × Apertus – Controlled Email Drafting Demo

Aufgabe
  Erstelle ausschliesslich E-Mail-Entwürfe auf Grundlage der fiktiven
  Projektdaten. Niemals E-Mails versenden.

Kurzanleitung
  1. Beschreibe den gewünschten Entwurf oder nenne einen fiktiven Kontakt.
  2. Hermes prüft zuerst die Datenminimierung.
  3. Nur freigegebene Felder dürfen an Apertus übergeben werden.
  4. Prüfe Entwurf und Nachweis der verwendeten Felder.
  5. Eine Freigabe erzeugt keinen Versand; dies ist eine No-send-Demo.

Projektregeln: /workspace/AGENTS.md
Fiktive Testdaten: /workspace/data/test_contacts.json

Hermes bereit. Welche Aufgabe soll ich bearbeiten?

EOF

exec hermes --cli
