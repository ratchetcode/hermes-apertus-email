# Hermes Agent x Apertus for privacy-conscious email marketing

## Technischer Kurzbericht

**Hack Apertus Online Hackathon · Track 2B · 15. Oktober 2026**
**Projekt:** Nick Menzi · **Status:** lokaler, fiktiver No-Send-Demonstrator

## 1. Ziel und Ergebnis

Hermes Agent x Apertus for privacy-conscious email marketing ist ein Docker-ausführbarer Hermes-Demonstrator für das kontrollierte Erstellen und Prüfen fiktiver E-Mail-Entwürfe der **Onlineshop Demo AG**. E-Mail-Automation kann Empfängerbezug, sensible Daten, Entwurf und Versand vermischen. Dieses Projekt trennt diese Schritte in fiktive Daten, minimierten Kontext, lokale Review-Queue und eine No-Send-Grenze.

**Erreicht:**

- Versioniertes Agentenprofil unter `agent-profile/`; gezielte lokale Übernahme in die isolierte Runtime.
- Eine sichtbare, kanonische fiktive Kontaktquelle mit **50 Kontakten**: 17 `recruit`, 17 `retain`, 16 `recover`.
- Deterministische kontaktbezogene Review-Queue: Gruppe auswählen, konkreten fiktiven Kontakt anzeigen, vor/zurück gehen, Entwurf lokal prüfen, bestätigen, überspringen oder abbrechen.
- Der Queue-Kontext enthält keine E-Mail-Adresse; die Modell- und Review-Grenze hält Adressen, interne Notizen und stabile technische IDs aus dem Entwurfsinhalt heraus.
- Kein SMTP, kein CRM, kein Webhook, keine Kontaktaufnahme und kein automatischer Export oder Versand.

## 2. Architektur und Workflow

Die lokale Docker-Runtime startet Hermes über `make run`. Das versionierte Profil bleibt getrennt von lokaler Runtime, Sitzungen, Logs und Zugangsdaten. Modellparameter gehören ausschließlich in die nicht versionierte `.env`.

### Kontrollierter Workflow

1. **Anfrage erfassen:** Ziel, Dienstleistung, Ton und gewünschte 3R-Zielgruppe klären.
2. **Empfänger binden:** Die kanonische CSV liefert die exakte Gruppe und Kontaktanzahl.
3. **Review-Queue starten:** Ein fiktiver Kontakt wird als „Entwurf n von Gesamtzahl“ angezeigt – ohne Adresse.
4. **Entwurf prüfen:** Text lokal erfassen oder überarbeiten; Änderungen bleiben beim aktuellen Queue-Element.
5. **Entscheiden:** Bestätigen, überspringen, zum vorherigen/nächsten Kontakt wechseln oder abbrechen.
6. **Export erst später:** Nur nach vollständiger menschlicher Prüfung und separater Freigabe. Ein Versandpfad existiert nicht.

Die freie TUI-Unterhaltung bleibt ein unterstützender Entwurfsdialog. Die deterministische Queue ist der kontrollierte Pfad für Empfängerauswahl, Reihenfolge und Review-Status.

## 3. Daten- und Sicherheitsgrenzen

Die sichtbare Demoquelle `data/demo_contacts_3r.csv` enthält ausschließlich fiktive, mit `fictional_demo_only` markierte Kontakte. Alle Adressen enden auf `@example.invalid`. Die technische Testfixture liegt getrennt unter `tests/fixtures/` und ist keine zweite sichtbare Demoquelle.

Die Review-Queue speichert nur die für die Darstellung benötigten fiktiven Felder: Kontakt-ID, Name, Firma, Sprache, 3R-Kategorie, Lifecycle-Status, Interesse und Tags. Nicht in Queue-Ansicht oder Modellkontext: E-Mail-Adresse, interne Notizen, Zugangsdaten oder reale Kundendaten.

**Sichere Standardgrenze:** Draft-only und `no_send`. Ein erfolgreicher Entwurf ist weder versandt noch zugestellt. Der verwendete Modellendpunkt wird nicht durch dieses Repository bereitgestellt oder bestätigt; ein Live-Modellaufruf war kein Bestandteil der aktuellen Verifikation.

## 4. Verifikation, Reproduzierbarkeit und Grenzen

Die aktuelle Offline-Suite ergab **43/43 bestandene Tests**. Geprüft wurden unter anderem CSV-Struktur und 3R-Zahlen, Datenminimierung, No-Send-Status, Queue-Navigation, lokale Entwurfsbestätigung, Profilübernahme, Plugin-Import sowie Docker-Compose-Konfiguration.

Zusätzlich wurde für die Queue bestätigt: `retain: 17`, Position `1/17`, kein E-Mail-Feld im aktuellen Review-Kontakt und `no_send=True`. Die lokale Plugin-Prüfung bestätigte Import und Registrierung. Der reale Docker-TUI-Start muss auf dem berechtigten Host erfolgen; in der aktuellen Automationsumgebung war der Docker-Socket nicht verfügbar.

### Reproduzierbarer Testablauf

1. `make test` – Offline-Tests ohne Modellaufruf.
2. `make profile-apply` – Profildateien gezielt in die lokale Runtime übernehmen.
3. Aus `track_2b/` `make run` starten; vollständige Docker- und lokale `.env`-Konfiguration stehen in `README.md`.
4. In der TUI die Kontaktübersicht und danach eine kontaktbezogene Review-Queue für `recruit`, `retain` oder `recover` starten.

### Offene Grenzen und nächster Schritt

Die natürliche Modellunterhaltung kann ohne kontrollierten Queue-Pfad weiterhin unpassende Geschäftsdetails formulieren. Der nächste sinnvolle Ausbau ist daher eine echte Einbettung der Queue in den normalen TUI-Dialog, sodass Empfängerbindung und Review automatisch vor jedem konkreten Entwurf erfolgen. Reale Kontakte, Datenimporte, Versand, CRM-Anbindung oder ein Messaging-Gateway bleiben ausdrücklich außerhalb dieses Demonstrators.
