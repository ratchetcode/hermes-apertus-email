#!/bin/sh
set -eu

: "${LLM_NAME:?LLM_NAME must be set in .env}"
: "${LLM_BASE_URL:?LLM_BASE_URL must be set in .env}"
: "${LLM_API_KEY:?LLM_API_KEY must be set in .env}"

cat <<'EOF'

Hermes Agent x Apertus for privacy-conscious email marketing – Controlled Email Drafting Demo

Diese isolierte Demonstration verwendet ausschliesslich fiktive Daten aus
diesem Repository. Sie erstellt einen nachvollziehbaren E-Mail-Entwurf.
Niemals E-Mails versenden, CRM-Daten ändern oder Empfänger kontaktieren.

Step 1 — deterministic preflight
- recipient data is held back from the model;
- only campaign-approved fields are supplied to Apertus;
- the output remains pending human approval for draft, recipient and purpose.

Project rules: /workspace/AGENTS.md
Technical test fixture: /workspace/tests/fixtures/test_contacts.json
Visible canonical demo contacts: /workspace/data/demo_contacts_3r.csv

EOF

python3 /workspace/src/workflow.py --contact-id demo-contact-001

printf '\nGenerate a live Apertus draft? [y/N] '
read -r answer
case "$answer" in
  y|Y|yes|YES)
    python3 /workspace/src/workflow.py --contact-id demo-contact-001 --live
    ;;
  *)
    printf '%s\n' 'Stopped after preflight. No model call and no email was sent.'
    ;;
esac
