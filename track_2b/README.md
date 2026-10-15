# Apertus Draft Gate — Hermes Email-Marketing Framework

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
- loads the project-local `email-framework` plugin with deterministic preflight,
  explicit `/email-approve <approval-id>` for single drafts and
  `/email-approve-segment <approval-id>` for 3R cohorts;
- offers Recruit, Retain and Recover as three fictional categories with exactly
  eight contacts each (24 total), then creates eight personalised draft-only
  review items after explicit segment approval;
- retains a deterministic policy gate for the fictional fixture data;
- sends only campaign-approved fields to Apertus through the deterministic
  draft command;
- shows a data-minimisation record, `pending` human approval and `no_send: true`;
- requires a new preflight and confirmation for every follow-up draft.

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

### 3R cohort demonstration in Hermes

In `make run`, ask for a fictional campaign for **Recruit**, **Retain** or
**Recover**, then provide goal, language and tone. Hermes calls the deterministic
segment preflight and displays eight minimised fictional contexts. After review,
type the exact command returned by the preflight, for example:

```text
/email-approve-segment segment-…
```

Only then can Hermes create eight personalised drafts. They are retained in the
project-local review state with `needs_review`, `delivery_mode: draft_only` and
`no_send: true`. The event log records `preflight_created`,
`approved_for_batch_generation`, `generation_claimed` and `drafts_created`; it
has no delivery event types.

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

## License

CC-BY-4.0, as required by the Hack Apertus template.
