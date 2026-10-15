# Hermes-Profil und persistente Runtime – Vorbereitung

## Zweck

`make run` startet die **Hermes-TUI**. Hermes bleibt die Bedienoberfläche, die
Sitzungsinstanz und der Träger des Projektprofils. Die Python-Workflow-Dateien
sind höchstens lokale technische Hilfsmittel; sie ersetzen Hermes nicht.

## Persistente Projekt-Runtime

Der Compose-Mount verbindet:

```text
Projekt:    ./runtime/hermes/
Container:  /opt/data/
HERMES_HOME=/opt/data
HOME=/opt/data
```

Damit bleiben zwischen Containerläufen im Projekt erhalten:

- `SOUL.md` – Hermes-Identität und grundlegende Arbeitsweise;
- `config.yaml` – lokale Hermes-Konfiguration ohne Geheimnisse;
- `state.db` und `sessions/` – Hermes-Sitzungen und Chat-Zustand;
- `skills/`, sofern Hermes dort projektlokale Skills installiert;
- lokale, technische No-Send-Draft-Zustände unter `email-framework/`.

Die Runtime ist projektlokal und wird nicht mit dem normalen Host-Profil
`/home/nick/.hermes/` vermischt.

## Verantwortlichkeiten

| Ort | Aufgabe | Verantwortlich |
|---|---|---|
| `runtime/hermes/SOUL.md` | Identität, Arbeitsprinzipien, Grenzen, gewünschter E-Mail-Ablauf | Herr Menzi / Hermes-Profilpflege |
| `runtime/hermes/config.yaml` | Modell, Anzeige, Toolsets und lokale Laufzeitkonfiguration | Hermes-Profilpflege |
| `AGENTS.md` | Projektregeln für technische Dateien und No-Send-Grenzen | Projekt |
| `runtime-template/` | Initiale Vorlage für eine noch leere Runtime | Projekt; keine tägliche Arbeitsakte |
| `runtime/hermes/sessions/`, `state.db` | Persistierter Chat- und Sitzungszustand | Hermes; nicht manuell bearbeiten |
| `docs/` | Nachvollziehbare Entscheidungen und technische Dokumentation | Projekt |

## Startverhalten

```bash
sudo make run
```

startet Hermes mit:

```text
/bin/sh /workspace/scripts/start-hermes.sh hermes --tui
```

Das Startskript legt bei einer **leeren** Runtime die Grundvorlagen an. Eine
bestehende projektlokale `SOUL.md` wird nicht bei jedem Start überschrieben.

## GitHub-sichere Profil-Sicherung

Die aktive Runtime bleibt absichtlich unter `runtime/` von Git ausgeschlossen,
weil sie Chats, Sitzungen, Logs und potenziell Geheimnisse enthalten kann.

Nach einer bewusst vorgenommenen Profiländerung erzeugt:

```bash
make profile-snapshot
```

einen **versionierbaren** Ordner `agent-profile/`. Exportiert werden nur:

```text
SOUL.md
config.yaml (nur mit Umgebungsplatzhaltern für Geheimnisse)
instructions/**/*.md
```

Der Export verweigert eine `config.yaml` mit einem wörtlich eingetragenen
Geheimnis. Sitzungen, `state.db`, Logs, Credentials und Exporte werden nicht
kopiert. Die zwei projektgebundenen Minimal-Skills liegen getrennt und
versioniert unter `profile-skills/`; das Startskript kopiert sie in die aktive
Runtime. Erst dieser geprüfte Snapshot plus `profile-skills/` gehört in einen
späteren Git-Commit und nach ausdrücklicher Freigabe in den GitHub-Push.

## Arbeitsregel für die weitere Konfiguration

1. Herr Menzi definiert SOUL und Profilinhalt.
2. Hermes arbeitet aus diesem persistenten Projektkontext heraus.
3. Chat-Verläufe und dokumentierte Entscheidungen bleiben in der Runtime.
4. Neue dauerhafte Arbeitsanweisungen werden als überprüfbare Markdown-Dateien
   abgelegt, nicht nur als flüchtige Chatantwort.
5. Ein Modelltext, eine Tool-Ankündigung oder eine behauptete Aktion gilt nicht
   als technische Tatsache ohne überprüfbaren lokalen Zustand oder Test.
6. Die No-Send-Grenze bleibt unabhängig von Profiltexten aktiv: kein SMTP,
   kein automatischer Versand, keine externen Kontakte.

## Offener Architekturpunkt

Die freie Hermes-TUI kann derzeit mit dem Modelltext konkurrieren. Das darf
nicht durch einen separaten Ersatzprozess kaschiert werden. Die spätere
Integration muss Hermes als Oberfläche und Profilinstanz beibehalten; lokale
Draft-Werkzeuge dürfen nur kontrollierte, überprüfbare Zustände liefern.
