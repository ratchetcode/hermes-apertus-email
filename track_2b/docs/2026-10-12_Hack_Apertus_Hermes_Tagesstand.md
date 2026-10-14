# Hack Apertus × Hermes — Tagesstand

**Datum:** 12. Oktober 2026
**Status:** aktiver Hackathon-Arbeitsstand lokal geprüft; keine externen Nachrichten versendet und kein Live-Modellendpunkt aufgerufen.
**Quellenstatus:** Git-Arbeitsstand, Commit-Historie und lokale Testausgabe verifiziert. Zugangsdaten bleiben undokumentiert.

## Projektziel

Track 2B demonstriert einen kontrollierten, **ausschliesslich entwerfenden** E-Mail-/Newsletter-Workflow mit Hermes und einem vom Betreiber konfigurierten Apertus-kompatiblen Endpunkt.

```text
Fiktive Kontaktdaten
→ deterministischer Datenminimierungs- und Freigabe-Preflight
→ optionaler Modellaufruf nur nach neuer expliziter Bestätigung
→ Entwurf mit Status pending und no_send: true
```

Nicht Teil des Projekts sind Versand, CRM-Zugriff, Kontaktimport, Webhook, Queue oder automatische externe Aktion.

## Heute verifizierter Repository-Stand

```text
Lokaler Workspace:
/home/nick/hack-apertus/hermes-apertus-email-1

Aktiver Branch:
feat/run-to-finish

Aktueller Commit:
af3829f — feat: add interactive Hermes Apertus draft framework
Commitzeit:
2026-10-12 14:36:28 UTC

Git-Arbeitsverzeichnis:
keine uncommitteten Änderungen angezeigt
```

## Heute im aktuellen Commit enthalten

- Interaktive projektlokale Hermes-Apertus-Demo über `make run` bzw. `make chat`.
- Isolierter Hermes-Runtimebereich unter `track_2b/runtime/hermes`; der normale Host-Hermes-Kontext wird nicht eingebunden.
- Separater Gateway-Modus über `make gateway`, ausdrücklich nur für eine später separat konfigurierte Messaging-Plattform.
- Deterministischer Draft-Preflight über `make draft` mit erneuter expliziter Bestätigung vor einem optionalen Modellrequest.
- Datenminimierung in `src/policy.py` und `src/workflow.py`: `email`, `id` und `internal_note` sind vom Modellkontext ausgeschlossen.
- Klare Ausgabe von verwendeten/ausgeschlossenen Feldern, `pending`-Freigabestatus und `no_send: true`.
- Aktualisierte Projektdokumentation, technischer Bericht sowie lokale Demo-/Report-Artefakte.

## Lokale Testverifikation vom 12. Oktober 2026

Ausgeführt im Verzeichnis `track_2b/`:

```bash
make test
```

Ergebnis:

```text
Ran 15 tests in 0.017s
OK
```

Abgedeckte Nachweise umfassen unter anderem:

```text
- isolierten persistenten Hermes-Gateway-Start im Container
- explizite Live-Bestätigungsgrenze des Draft-Startskripts
- projektlokalen Runtime-Bootstrap
- Makefile-Trennung zwischen interaktivem Betrieb und Gateway
- verpflichtenden Preflight und erneute Freigabe für Follow-ups
- lokale Umgebungsreferenzen für die Apertus-Konfiguration
- Ausschluss nicht erlaubter Felder aus dem Modellkontext
- Status pending und no_send: true
- kontrollierten Fehlerpfad bei ungültiger Modellantwort bzw. Endpoint-Fehler
```

## Bewusst nicht getestet / nicht behauptet

```text
- Kein realer E-Mail-Versand
- Kein Zugriff auf reale Kunden-, CRM-, Mailbox- oder Zahlungsdaten
- Kein Aufruf eines Live-Apertus-Endpunkts in dieser Verifikation
- Keine Behauptung einer produktionsreifen Datenschutz-, Freigabe- oder
  Versandlösung
```

## Bekannte Grenze und nächster sinnvoller Schritt

Die deterministische Policy und der Preflight sind die sicherheitsrelevante Grenze; reine Anweisungen in `AGENTS.md` reichen dafür nicht aus. Ein späterer echter Modellaufruf darf ausschliesslich den bereits minimierten fiktiven `model_context` verwenden und benötigt pro Entwurf eine neue explizite Freigabe.

Weiterer Ausbau bleibt optional und ist nicht aktiviert:

```text
- Review-UI mit Bindung an Entwurfs-Hash, Empfänger und Zweck
- zusätzliche Red-Team-Testfälle
- on-premise/offline Bereitstellungsrezept
- bewerteter Testsatz für Entwurfsqualität
- revisionssicheres Auditprotokoll ohne unnötige Kontaktinhalte
```

## Bezug zum vorherigen Stand

Dieser Tagesstand führt fort:

```text
HackApertus/2026-10-10_Hack_Apertus_Hermes_Arbeitsstand.md
```

Der Stand vom 10. Oktober 2026 dokumentierte den No-send-Preflight mit 9 Tests. Der heutige Stand dokumentiert den erweiterten interaktiven Rahmen und die erfolgreiche lokale Suite mit 15 Tests.
