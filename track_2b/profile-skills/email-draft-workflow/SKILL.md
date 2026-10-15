---
name: email-draft-workflow
description: "Use when creating, reviewing, revising, or locally exporting fictional no-send email drafts."
version: 1.0.0
---

# Kontrollierter E-Mail-Entwurfsablauf

Verwende diesen Skill für den in der SOUL definierten Entwurfsprozess.

## Prozess

1. Erfasse nur noch fehlende Angaben: Entwurfsart, bei Bedarf 3R-Kategorie,
   Ziel, fiktive Zielgruppe, Angebot, Ton und besondere Vorgaben.
2. Wiederhole keine bereits beantwortete Frage. Frage nur den nächsten offenen
   Punkt.
3. Fasse die vollständigen Vorgaben zusammen und nenne Annahmen oder fehlende
   Angaben.
4. Erstelle einen Entwurf erst nach ausdrücklicher Freigabe.
5. Zeige Entwürfe mit Betreff, Anrede, Haupttext, Handlungsaufforderung und
   Schlussformel.
6. Nach einer Änderung zeige immer den vollständigen aktualisierten Entwurf.
7. Biete einen lokalen `.eml`-Export erst nach Sichtprüfung und einer weiteren
   ausdrücklichen Freigabe an.

## Grenzen

- Ausschliesslich fiktive Kontakte und Kampagnendaten, sofern nicht ausdrücklich
  anders autorisiert.
- `no-send`: Kein SMTP, kein Versand, keine CRM-, Newsletter-, Webhook- oder
  Kontaktaktion.
- Keine internen Toolnamen, Befehle, Dateipfade, JSON-Ausgaben oder technischen
  Fehlerdetails im normalen Operator-Dialog.
- Wenn eine nötige technische Funktion nicht verfügbar ist, benenne den sicheren
  nächsten Schritt statt einen Export, eine Datei oder eine Aktion zu erfinden.
