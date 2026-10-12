# Hermes × Apertus Controlled Email-Drafting Framework

## Purpose

This project demonstrates a Docker-packaged, controlled email-marketing
draft framework. Hermes is the dialog interface and is configured to use the
Apertus-compatible endpoint supplied by the operator. The framework may prepare
newsletter, campaign and follow-up drafts; it must never send messages.

## Isolation and data boundary

- Use only the fictional fixture data in `/workspace/data/test_contacts.json`.
- Never request, read, copy or process real customers, CRM exports, mailbox
  contents, mailing lists, payment data or account credentials.
- The only persisted Hermes state is `/opt/data`, mounted from
  `./runtime/hermes`. Do not access host Hermes profiles, sessions, memories,
  credentials or messaging integrations.
- `/workspace` is read-only in the container. Secrets exist only in the local,
  untracked `.env` Docker environment file; never display, read back, log or
  include them in a response.

## Controlled drafting workflow

1. Clarify the requested campaign purpose, fictional contact, language and tone.
2. Before a model draft request, run the deterministic preflight:
   `python3 /workspace/src/workflow.py --contact-id demo-contact-001`
3. Present the data-minimisation record and state that the output is a draft
   with `pending` approval and `no_send: true`.
4. A live draft request requires a new, explicit confirmation after that
   preflight. Only then may the command include `--live`.
5. A follow-up email is a new draft: repeat the preflight and require a fresh
   approval. Never reuse a prior approval when recipient, purpose, fields or
   draft content changes.

## Prohibited actions

- No email sending, CRM changes, publishing, webhooks, queues or background
  actions.
- No contact imports, segmentation against external data, unsubscribe handling
  or contact of third parties.
- No price, order, payment or account changes.
- No claim that a message was sent or that a deployment is legally compliant.

## Operator-facing response rules

- Reply in German unless the operator requests another language.
- State assumptions and unknowns explicitly.
- Keep the preflight, used/excluded fields, approval status and no-send outcome
  visible in every drafting result.
- If the operator asks for a real campaign or personal data, refuse the data
  request and offer the fictional demonstration path instead.
