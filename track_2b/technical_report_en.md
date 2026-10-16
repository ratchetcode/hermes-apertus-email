# Hermes Agent x Apertus for privacy-conscious email marketing

## Technical Brief

**Hack Apertus Online Hackathon · Track 2B · 15 October 2026**
**Project:** Nick Menzi · **Status:** local fictional no-send demonstrator

## 1. Purpose and result

Hermes Agent x Apertus for privacy-conscious email marketing is a Docker-runnable Hermes demonstrator for controlled creation and review of fictional email drafts for **Onlineshop Demo AG**. It is deliberately not a newsletter or email-delivery system.

**Implemented:**

- Versioned agent profile and controlled transfer into an isolated local runtime.
- One canonical fictional contact source with **50 contacts**: 17 `recruit`, 17 `retain`, 16 `recover`.
- Deterministic per-contact review queue: select a group, show the current fictional contact, navigate previous/next, store and review a draft locally, confirm, skip or abort.
- The queue view contains no email address; the model and review boundary excludes addresses, internal notes and technical stable identifiers from draft content.
- No SMTP, CRM, webhook, contact action, automatic export or sending.

## 2. Architecture and workflow

The local Docker runtime starts Hermes through `make run`. The versioned profile is separated from the local runtime, sessions, logs and credentials. Model parameters belong only in the untracked `.env` file.

### Controlled workflow

1. Capture request: clarify goal, service, tone and intended 3R group.
2. Bind recipients: the canonical CSV supplies the exact group and count.
3. Start review queue: show one fictional contact as “Draft n of total” without its address.
4. Review draft: capture or revise text locally; changes remain with the current queue item.
5. Decide: confirm, skip, move previous/next or abort.
6. Export later: only after complete human review and separate approval. No sending path exists.

Free TUI conversation remains a drafting aid. The deterministic queue is the controlled path for recipient selection, sequence and review state.

## 3. Data and safety boundaries

The visible source `data/demo_contacts_3r.csv` contains only fictional contacts marked `fictional_demo_only`. Every address ends in `@example.invalid`. The technical fixture is isolated under `tests/fixtures/` and is not a second visible demo source.

The review queue retains only fictional fields needed for review: contact ID, name, company, language, 3R category, lifecycle stage, interest and tags. It excludes email addresses, internal notes, credentials and real customer data.

**Safe default:** draft-only and `no_send`. A successful draft is neither sent nor delivered. The model endpoint is not provided or verified by this repository, and a live model request was not part of current verification.

## 4. Verification, reproducibility and limits

The current offline suite produced **43/43 passing tests**. It covers CSV structure and 3R counts, data minimisation, no-send state, queue navigation, local draft confirmation, profile application, plugin import and Docker Compose configuration.

A queue check additionally confirmed `retain: 17`, position `1/17`, no email field in the current review contact and `no_send=True`. The local plugin check confirmed import and registration. The real Docker TUI must be started on an authorised host; the Docker socket was unavailable in the automation environment.

### Reproducible test sequence

1. `make test` – offline checks without a model call.
2. `make profile-apply` – controlled profile transfer to the local runtime.
3. `sudo make run` – start Hermes TUI on the authorised host.
4. In the TUI, inspect a 3R group and start a per-contact review queue.

### Open limitation and next step

Outside the controlled queue path, natural model conversation can still formulate unsuitable business details. The next useful step is to embed the queue in normal TUI dialogue, so recipient binding and review start before every concrete draft. Real contact imports, delivery, CRM integration and messaging gateways remain explicitly outside this demonstrator.
