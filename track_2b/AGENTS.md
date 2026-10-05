Hermes × Apertus Demo Rules
Purpose

This project demonstrates controlled email drafting with Hermes Agent and the Apertus model family.
Data boundary

- Use only fictional test data stored in this repository.
- Never use real customer, CRM, mailbox, contact, payment or account data.
- Do not load, copy or access the operator's existing Hermes profiles, sessions, memory, credentials or messaging integrations.
Allowed workflow

1. Select a fictional test contact.
2. Check which fields are approved for the stated campaign purpose.
3. Send only approved fields to the configured Apertus endpoint.
4. Return an email draft and a transparent record of the fields used.
5. Require explicit human approval for the exact draft, recipient and purpose.
Prohibited actions

- No email sending.
- No CRM updates.
- No external messaging.
- No price, order, payment or account changes.
- No hidden background actions.
- No reuse of an approval after recipient, purpose, data fields or draft content changes.
Model boundary

- Use Apertus through the configured LLM_NAME, LLM_BASE_URL and LLM_API_KEY environment variables.
- Secrets belong only in local .env files and must never be committed.
Evidence

The user interface must make the data minimisation check, draft, approval status and no-send outcome visible.