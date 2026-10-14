# Nutzer-Onboarding und Zielmodell für Kampagnen

## 1. Produktziel

Nach dem Klonen soll ein Betreiber grundsätzlich nur noch vier Dinge erledigen:

1. lokale Zugangsdaten in `.env` eintragen;
2. seine Kontaktdatei in einem dokumentierten Importformat bereitstellen;
3. Kampagnenziel, Zielgruppe, Sprache und Ton beschreiben;
4. Entwürfe, Empfängervorschau und später jeden Versand explizit freigeben.

Docker, Hermes, die kontrollierten Workflows, Validierungen, Vorlagen,
Datenminimierung und die Freigabegrenzen gehören zum Projekt und werden über
GitHub bereitgestellt. Zugangsdaten, reale Kontakte, Laufzeitdaten und
Freigabeprotokolle bleiben lokal.

## 2. Konfigurationsgrenze

Die lokale, nicht versionierte Datei `.env` enthält nur Zugangsdaten und
installationsspezifische Werte. Sie wird niemals committed. Die versionierte
`.env.example` enthält ausschließlich Platzhalter und Beschreibungen.

Geplante Kategorien:

| Kategorie | Beispiele | Zweck |
|---|---|---|
| LLM | `LLM_NAME`, `LLM_BASE_URL`, `LLM_API_KEY` | Entwurfserzeugung über Apertus oder einen anderen freigegebenen Endpunkt. |
| Telegram | `TELEGRAM_BOT_TOKEN`, `TELEGRAM_ALLOWED_CHAT_IDS` | Optionaler Bedien- oder Benachrichtigungskanal. |
| Posteingang | `IMAP_HOST`, `IMAP_USERNAME`, `IMAP_PASSWORD` | Optionaler, standardmäßig lesender Mailbox-Zugriff. |
| Versand | `SMTP_HOST`, `SMTP_USERNAME`, `SMTP_PASSWORD`, `SMTP_FROM_ADDRESS` | Später separat aktivierbarer Versandadapter. |
| Sicherheitsmodus | `EMAIL_DELIVERY_MODE`, `EMAIL_SEND_ENABLED` | Technischer Aus-Zustand und spätere kontrollierte Freischaltung. |

IMAP, SMTP und Telegram sind getrennte Integrationen. Ein Zugang zum
Posteingang autorisiert weder einen Versand noch automatische Antworten. Für
Mailanbieter sind bevorzugt getrennte App-Passwörter oder OAuth-Zugänge mit
minimalen Rechten zu verwenden; kein normales Hauptpasswort in Chat,
Dokumentation oder Git speichern.

## 3. Aktueller Stand

Der aktuelle Release ist ein **no-send-Demonstrator**:

```text
Preflight → ausdrückliche Entwurfsfreigabe → ein Entwurf → no_send: true
```

Er importiert noch keine realen Kontaktdateien und enthält keinen SMTP-,
IMAP- oder Telegram-Adapter. Die oben genannten Zugangsdatenfelder werden als
klare Onboarding-Schnittstelle vorbereitet; ihre spätere Nutzung benötigt einen
eigenen Implementierungs-, Test- und Freigabeblock.

### Gesprächs-Initiation

Bei einer neuen Unterhaltung, einer Begrüßung oder einer Frage nach dem Zweck
des Systems erklärt Hermes kurz in der Sprache der aktuellen Anfrage:

1. Es erstellt kontrollierte E-Mail-Entwürfe und versendet nichts.
2. Der Betreiber beschreibt Kampagne, Kontakt-ID, Sprache und Ton.
3. Hermes zeigt zuerst einen Preflight zur Prüfung.
4. Erst nach `/email-approve <approval-id>` darf ein einzelner Entwurf entstehen.

Danach fragt Hermes gezielt nach Kampagnenziel, fiktiver Kontakt-ID, Sprache und
Ton. Eine Begrüßung allein löst keinen Preflight oder Modellaufruf aus.

## 4. Kontaktimport und Datenformate

Der erste verpflichtende Importweg ist CSV. JSON und XLSX können später als
zusätzliche Adapter auf dasselbe interne Schema folgen. Beliebige Dateien oder
unbekannte Spalten werden nicht stillschweigend übernommen.

### 4.1 CSV-Mindestschema

```csv
contact_id,email,first_name,company,language,lifecycle_stage,interest,consent_status,consent_timestamp,unsubscribed,campaign_tags
```

| Feld | Bedeutung |
|---|---|
| `contact_id` | lokale, stabile Kontaktkennung |
| `email` | Zustelladresse; nie unnötig Teil des LLM-Prompts |
| `first_name`, `company`, `interest` | optionaler Personalisierungskontext nach Freigabe |
| `language` | bevorzugte Kommunikationssprache |
| `lifecycle_stage` | Marketingphase des Kontakts |
| `consent_status`, `consent_timestamp` | lokaler Nachweis für die Versandprüfung |
| `unsubscribed` | Sperrstatus; sperrt jede Kampagnenauswahl |
| `campaign_tags` | optionale, nachvollziehbare Segmentierung |

Ein Import muss zuerst als Dry Run validieren und eine Empfängervorschau mit
Fehlern, ausgeschlossenen Datensätzen und Anzahl liefern. Das fiktive Schema ist
auch als `data/templates/contacts.example.csv` vorhanden. Reale Importdateien
bleiben lokal und werden nicht nach GitHub geladen.

## 5. Marketingphasen

Jeder Kontakt gehört zu genau einer aktuellen Hauptphase. Zusätzliche Tags sind
möglich, ersetzen aber keine Hauptphase.

| Phase | Technische Bedeutung | Typische zulässige Entwurfsart |
|---|---|---|
| `acquisition` | Erstansprache/noch kein Kunde | Nur nach der für den Betreiber definierten Kontakt- und Einwilligungsregel; keine automatische Massenaktion. |
| `interest` | Interesse ist dokumentiert | Informations-, Einladungs- oder Vergleichsentwurf. |
| `onboarding` | neue Anmeldung oder neuer Kunde | Willkommens-, Einrichtungs- oder erster Nutzenhinweis. |
| `active_customer` | aktive Kundenbeziehung | Produkt-, Service- oder Nutzungsinformation. |
| `after_sales` | nach Kauf oder Leistung | Hilfe-, Pflege-, Feedback- oder Ergänzungsentwurf. |
| `retention` | Beziehung sichern | Relevanz-, Verlängerungs- oder Mehrwertentwurf. |
| `reactivation` | länger inaktiv | klar begrenzter Reaktivierungsentwurf. |
| `suppressed` | Abmeldung, Sperre oder unklare Berechtigung | Niemals als Empfänger auswählen. |

Eine Willkommens-E-Mail wäre daher typischerweise eine Kampagne mit:

```text
Zielphase: onboarding
Filter: consent_status=opt_in UND unsubscribed=false
Versandmodus: zunächst Entwurf und Testversand
```

Nicht jede Zeile einer CSV ist automatisch ein zulässiger Empfänger. Der
Empfängerfilter muss Sperrstatus, Einwilligung, Zielphase und die explizit
freigegebene Kampagne berücksichtigen.

## 6. Zielprozess für eine Kampagne

```text
Kontaktimport (Dry Run)
  → Schema-/Einwilligungs-/Sperrprüfung
  → Kampagnenbeschreibung durch Betreiber
  → Segmentvorschau nach Marketingphase
  → Datenminimierungs-Preflight
  → Apertus-Entwurf
  → Entwurfsfreigabe
  → Empfängerfreigabe mit Anzahl und Filterregel
  → einmaliger Testversand an ausdrücklich gewählte Testadresse
  → separate Versandfreigabe
  → SMTP-Versand und lokales Versandprotokoll
```

Bis der Versandadapter ausdrücklich implementiert, getestet und freigegeben
ist, endet der Workflow beim Entwurf. `EMAIL_DELIVERY_MODE=draft_only` und
`EMAIL_SEND_ENABLED=false` bleiben der sichere Standard.

## 7. Akzeptanzkriterien für den späteren Versandblock

Ein Versandblock gilt erst als bereit, wenn er mindestens Folgendes erfüllt:

- `.env`-Prüfung ohne Ausgabe von Geheimnissen;
- CSV-Dry-Run mit verständlichem Fehlerbericht;
- Ausschluss von `suppressed`, abgemeldeten oder nicht freigegebenen Kontakten;
- nachvollziehbare Segmentvorschau mit Anzahl;
- Trennung von Modellkontext und Zustelladresse;
- explizite Entwurfs-, Empfänger- und Versandfreigabe;
- ein einziger, explizit adressierter Testversand vor einem Versandlauf;
- kein automatischer Retry bei unklarer SMTP-Antwort;
- lokales, minimiertes Versandprotokoll ohne Passwörter oder unnötige Inhalte;
- standardmäßig deaktivierter Versandadapter.
