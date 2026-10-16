# Hermes Agent x Apertus for privacy-conscious email marketing

## Hermes Email-Marketing Framework

A Docker-packaged, controlled **email and newsletter drafting framework** for
Hack Apertus Online Hackathon Track 2B. It starts an isolated interactive Hermes
session by default and can run a persistent Hermes gateway when a messaging
platform is explicitly configured.

The project is deliberately **draft-only**. It demonstrates the controlled core
of an email-marketing workflow without shipping an email sender, CRM client,
contact import, webhook, queue or automatic action.

## What the prototype does

- starts an isolated interactive Hermes session with `make run`;
- provides `make gateway` for a separately configured persistent Hermes gateway;
- configures Hermes with an operator-selected, OpenAI-compatible Apertus
  endpoint from a local `.env` file;
- provides a terminal chat mode that replies in the operator's current language;
  the last operator request decides, not the preceding assistant reply or quoted
  text in the request, while planning fictional newsletters, campaigns and
  follow-up drafts;
- loads the project-local `email-framework` plugin with local, deterministic
  no-send commands for the canonical 3R CSV contact review;
- exposes a per-contact review queue for the 50 visible fictional contacts:
  `recruit` 17, `retain` 17 and `recover` 16;
- snapshots only the allowed fictional presentation fields for the selected
  cohort; the recipient address is excluded from the review view and model
  context;
- keeps every item local with `draft_only` and `no_send: true`; no command sends
  mail, updates a CRM, calls a webhook or publishes content.

## Safety boundary

- `data/demo_contacts_3r.csv` is the only canonical, visible demo-contact
  dataset: 50 fictional contacts ordered by the 3R categories.
- `tests/fixtures/test_contacts.json` is a separate technical fixture for the
  deterministic no-send tests; it is not a second visible demo dataset.
- `src/policy.py` rejects `email`, record ID and internal notes even if a
  campaign configuration tries to approve them.
- The model payload created by `src/workflow.py` contains only the minimised
  context. Recipient address, record ID and internal notes are excluded.
- There is no SMTP, CRM, delivery, webhook or automatic-action implementation.
  The only queue is a project-local, fictional draft-review registry; it has no
  recipient delivery capability.
- The local `.env` file is ignored by Git. It must never be committed.
- No messaging channel is configured by default; a real integration requires a
  separate deployment and data-protection decision.

## Quick start

```bash
cd track_2b
cp .env.example .env
# Edit .env locally. Do not commit it.
make run
```

`make run` starts the interactive project-local Hermes session. Its runtime is
stored only in `./runtime/hermes`; it does not mount or reuse the operator's
normal Hermes profile. Leave the session with `/exit`.

`make chat` is an alias for the same interactive mode.

### Kontaktbezogene 3R-Prüfung in Hermes

In `make run` stehen lokale, deterministische Prüfschritte für die sichtbare
fiktive CSV bereit. Sie sind ein kontrollierter Ersatz für eine freie,
modellgesteuerte Empfängerauswahl und lösen keinen Modellaufruf aus.

```text
/email-demo-contacts
/email-demo-contacts retain
/email-demo-review-start retain | Neue Dienstleistung: Tassen bedrucken vorstellen
```

Der Start bindet die Prüfung an genau 17 fiktive `retain`-Kontakte und zeigt
`Entwurf 1 von 17` mit Name, Firma, Interesse, Ziel und Review-Status – aber
ohne Adresse. Danach sind `current`, `next`, `previous`, `draft`, `confirm`,
`skip` und `abort` als lokale Review-Schritte verfügbar. Eine Bestätigung bleibt
nur eine lokale Entwurfsbestätigung; sie löst keinen Export und niemals Versand
oder Zustellung aus.

To start the persistent gateway for a separately configured messaging platform:

```bash
make gateway
```

Stop a gateway with `Ctrl-C` or:

```bash
make stop
```

For the deterministic controlled draft demonstration, use:

```bash
make draft
```

The draft command first prints the preflight for `demo-contact-001` and asks:

```text
Generate a live Apertus draft? [y/N]
```

- Press **Enter** or anything other than `y`: no model request and no email.
- Enter `y`: one HTTPS request to `${LLM_BASE_URL}/chat/completions`, containing
  only the approved fictional context. The result is still a draft with
  `pending` approval and `no_send: true`.

## Configuration

`.env` contains only local endpoint credentials:

```dotenv
LLM_NAME=swiss-ai/Apertus-v1.5-8B
LLM_BASE_URL=https://your-controlled-apertus-endpoint/v1
LLM_API_KEY=replace-locally
```

On first start, `scripts/start-hermes.sh` copies
`runtime-template/config.yaml` into the local ignored runtime directory. The
configuration selects Hermes' `custom` provider and references the variables
above. Existing local runtime configuration is not overwritten.

## Verification

```bash
make test
```

Tests use fake model responses and require neither Docker access nor an API key.
They verify policy enforcement, payload minimisation, clean endpoint failures,
explicit live confirmation, and the isolated persistent gateway configuration.

## Architecture

```text
Operator
  │
  ├── make run / make chat ──> interactive Hermes (Apertus-configured conversation)
  ├── make gateway ──────────> optional persistent messaging gateway
  │
  └── make draft ────────────> deterministic preflight
                         │
                         ├── approved fictional fields only
                         ├── explicit live confirmation
                         └── Apertus draft → pending approval + no_send
```

A production-capable marketing system would additionally need independently
reviewed contact consent, recipient management, unsubscribe/suppression logic,
audit retention, role-based access, encryption, deletion/backup procedures and
a separately authorised sending adapter. Those features are intentionally not
implemented in this demonstrator.

## Structure

- `AGENTS.md` — project-local Hermes safety and workflow rules.
- `runtime-template/config.yaml` — non-secret isolated Hermes configuration.
- `scripts/start-hermes.sh` — idempotent project-runtime bootstrap and gateway
  start.
- `scripts/start-demo.sh` — explicit no-send draft demonstration.
- `src/policy.py` — allowlist/denylist data-minimisation policy.
- `src/workflow.py` — deterministic preflight and isolated Apertus draft call.
- `data/demo_contacts_3r.csv` — canonical visible fictional demo contacts.
- `data/templates/contacts.example.csv` — header-only CSV schema template.
- `tests/fixtures/test_contacts.json` — isolated technical test fixture.
- `tests/` — offline unit and configuration tests.

## Technical report / Technischer Bericht

Both report editions are reproducible, four-page PDFs with the same verified
technical scope, workflow and no-send boundary:

- `NickMenzi_Report_DE.pdf` — German technical report; source: `technical_report.md`.
- `NickMenzi_Report_EN.pdf` — English technical report; source: `technical_report_en.md`.

Recreate them locally:

```bash
python3 docs/create_report_pdf.py --language de technical_report.md NickMenzi_Report_DE.pdf
python3 docs/create_report_pdf.py --language en technical_report_en.md NickMenzi_Report_EN.pdf
```

## License

CC-BY-4.0, as required by the Hack Apertus template.
