# Entscheidung: Exportierbare E-Mail-Entwürfe

**Status:** Stufe 1 implementiert und durch lokale Tests verifiziert; Import in einen konkreten Mailclient noch offen.
**Geltung:** Ausschliesslich fiktive Demo-Kontakte und Draft-only-Workflow.

## Zielbild

Nach der expliziten Kampagnenfreigabe erzeugt das System acht personalisierte,
fiktive E-Mail-Entwürfe. Jeder Entwurf bleibt prüfbar und darf nicht automatisch
versendet werden.

## Stufe 1 – Lokaler, clientneutraler Export

- Entwürfe werden als einzelne RFC-5322-kompatible `.eml`-Dateien im
  isolierten Laufzeitordner `HERMES_HOME/email-framework/exports/<approval-id>/`
  gespeichert. Der Export erfolgt erst nach expliziter Freigabe und nach dem
  erfolgreichen Erzeugen aller acht fiktiven Entwürfe.
- Zusätzlich wird ein `manifest.json` mit Approval-ID, Entwurfs-ID, Status
  `needs_review`, Erstellzeit und Prüfsumme erzeugt.
- Der Export enthält keine Zustellaktion und keine SMTP-, CRM-, Webhook- oder
  Queue-Integration.
- Ein E-Mail-Programm kann `.eml` abhängig vom jeweiligen Client öffnen oder
  importieren; das konkrete Verhalten wird später mit einem ausgewählten Client
  separat geprüft.

## Stufe 2 – Optional: Entwürfe in ein echtes Postfach ablegen

- Erst nach ausdrücklicher Freigabe für ein konkretes eigenes oder autorisiertes
  Postfach darf ein Adapter Entwürfe in dessen Drafts-Ordner ablegen.
- Dazu ist ein Mailbox-Write-Zugang erforderlich; die Ablage erfolgt als Draft
  und nicht als Versand.
- Zugangsdaten bleiben ausserhalb des Repositorys in einer geschützten lokalen
  Secret-Ablage. Sie werden weder in `.env.example`, Logs, Chat noch technische
  Dokumentation übernommen.
- Nach jeder Ablage muss der Adapter den exakten Draft im Zielordner wieder
  lesen und Draft-Status, Betreff und sichere Kennung prüfen.

## Versandgrenze

SMTP ist ein Zustellprotokoll. Es erzeugt keine Drafts in einem Postfach.
Ein späterer SMTP-Sender wäre daher ein separater, ausdrücklich freizugebender
Schritt nach dem Draft-Export beziehungsweise der Draft-Ablage. Standard bleibt:

```text
Entwurf erzeugen → menschlich prüfen → Mensch versendet selbst im E-Mail-Programm
```

Automatischer Versand ist nicht Bestandteil der Demo und wird nicht implementiert.

## Noch zu entscheiden

1. Ziel-E-Mail-Programm für den Importtest.
2. Lokaler Exportpfad und Aufbewahrungsdauer der fiktiven `.eml`-Artefakte.
3. Ob eine spätere, separate IMAP-Draft-Ablage für ein konkretes autorisiertes
   Postfach gewünscht ist.
