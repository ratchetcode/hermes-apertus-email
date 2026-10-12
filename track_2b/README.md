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
- provides a terminal chat mode for planning fictional newsletters, campaigns
  and follow-up drafts in German;
- retains a deterministic policy gate for the fictional fixture data;
- sends only campaign-approved fields to Apertus through the deterministic
  draft command;
- shows a data-minimisation record, `pending` human approval and `no_send: true`;
- requires a new preflight and confirmation for every follow-up draft.

## Safety boundary

- All contacts in `data/test_contacts.json` are fictional.
- `src/policy.py` rejects `email`, record ID and internal notes even if a
  campaign configuration tries to approve them.
- The model payload created by `src/workflow.py` contains only the minimised
  context. Recipient address, record ID and internal notes are excluded.
- There is no SMTP, CRM, delivery, queue or webhook implementation.
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
- `data/test_contacts.json` — fictional fixture data.
- `tests/` — offline unit and configuration tests.

## License

CC-BY-4.0, as required by the Hack Apertus template.
