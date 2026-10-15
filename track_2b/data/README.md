# Demo contact data

`demo_contacts_3r.csv` is the **only canonical** contact list for the visible
email-drafting demo. It contains 50 fictional contacts, ordered by the three
3R categories: `recruit`, `retain`, `recover`.

Every row is fictional, uses an `@example.invalid` address, and is marked
`fictional_demo_only`. It must never be interpreted as a real customer list or
as permission to send email.

`templates/contacts.example.csv` is header-only. It is a CSV schema template,
not a second contact dataset.

Technical unit-test fixtures live under `tests/fixtures/` and are deliberately
outside this visible demo-data directory.
