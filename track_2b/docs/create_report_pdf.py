#!/usr/bin/env python3
"""Build a compact four-page PDF report for Hermes Agent x Apertus."

This generator intentionally uses only the Python standard library so the report
can be rebuilt in the constrained Docker/project environment.
"""

from __future__ import annotations

import argparse
import textwrap
from pathlib import Path

PAGE_WIDTH = 595
PAGE_HEIGHT = 842
LEFT = 46
RIGHT = 549
TOP = 790
BOTTOM = 52
BODY_SIZE = 9.2
LEADING = 13
OFFICIAL_PROJECT_NAME = "Hermes Agent x Apertus for privacy-conscious email marketing"


def escape_pdf(text: str) -> bytes:
    normalized = text.translate(str.maketrans({"–": "-", "—": "-", "•": "-", "→": "->"}))
    raw = normalized.encode("latin-1", "replace")
    return raw.replace(b"\\", b"\\\\").replace(b"(", b"\\(").replace(b")", b"\\)")


def text_command(x: float, y: float, text: str, *, size: float = BODY_SIZE, font: str = "F1") -> bytes:
    return (
        f"BT /{font} {size:.1f} Tf 1 0 0 1 {x:.1f} {y:.1f} Tm (".encode("ascii")
        + escape_pdf(text)
        + b") Tj ET\n"
    )


def wrapped(commands: list[bytes], x: float, y: float, text: str, *, width: int = 90, size: float = BODY_SIZE, leading: float = LEADING) -> float:
    for paragraph in text.split("\n"):
        if not paragraph:
            y -= leading * 0.45
            continue
        for line in textwrap.wrap(paragraph, width=width, break_long_words=False) or [""]:
            commands.append(text_command(x, y, line, size=size))
            y -= leading
    return y


def heading(commands: list[bytes], y: float, text: str, *, level: int = 2) -> float:
    size = 19 if level == 1 else 12.5
    commands.append(b"0.05 0.19 0.34 rg\n")
    commands.append(text_command(LEFT, y, text, size=size, font="F2"))
    commands.append(b"0 g\n")
    return y - (25 if level == 1 else 20)


def rule(commands: list[bytes], y: float) -> None:
    commands.append(f"0.10 0.35 0.56 RG 0.8 w {LEFT} {y:.1f} m {RIGHT} {y:.1f} l S\n".encode("ascii"))


def footer(commands: list[bytes], page: int, *, language: str = "de") -> None:
    rule(commands, 37)
    if language == "en":
        commands.append(text_command(LEFT, 22, f"{OFFICIAL_PROJECT_NAME} · Technical brief · 15 October 2026", size=6.6))
        commands.append(text_command(475, 22, f"Page {page} of 4", size=7.5))
        return
    commands.append(text_command(LEFT, 22, f"{OFFICIAL_PROJECT_NAME} · Technischer Kurzbericht · 15. Oktober 2026", size=6.6))
    commands.append(text_command(485, 22, f"Seite {page} von 4", size=7.5))


def box(commands: list[bytes], x: float, y: float, width: float, height: float, title: str, body: str, *, accent: bool = False) -> None:
    if accent:
        commands.append(b"0.90 0.95 0.98 rg\n")
    else:
        commands.append(b"0.96 0.97 0.98 rg\n")
    commands.append(f"{x:.1f} {y:.1f} {width:.1f} {height:.1f} re f\n".encode("ascii"))
    commands.append(b"0.18 0.39 0.56 RG 0.8 w\n")
    commands.append(f"{x:.1f} {y:.1f} {width:.1f} {height:.1f} re S\n".encode("ascii"))
    commands.append(b"0 g\n")
    commands.append(text_command(x + 9, y + height - 18, title, size=9.5, font="F2"))
    body_y = y + height - 34
    for line in textwrap.wrap(body, width=max(18, int(width / 5.5)), break_long_words=False):
        commands.append(text_command(x + 9, body_y, line, size=7.6))
        body_y -= 10


def arrow(commands: list[bytes], x: float, y_from: float, y_to: float) -> None:
    commands.append(b"0.18 0.39 0.56 RG 1.2 w\n")
    commands.append(f"{x:.1f} {y_from:.1f} m {x:.1f} {y_to:.1f} l S\n".encode("ascii"))
    commands.append(f"{x - 4:.1f} {y_to + 6:.1f} m {x:.1f} {y_to:.1f} l {x + 4:.1f} {y_to + 6:.1f} l S\n".encode("ascii"))


def page_one() -> bytes:
    c: list[bytes] = []
    y = TOP
    c.append(b"0.05 0.19 0.34 rg\n")
    c.append(text_command(LEFT, y, OFFICIAL_PROJECT_NAME, size=14, font="F2"))
    c.append(b"0 g\n")
    y -= 25
    c.append(text_command(LEFT, y, "Technischer Kurzbericht · Hack Apertus Online Hackathon · Track 2B", size=10, font="F2"))
    y -= 16
    c.append(text_command(LEFT, y, "Projekt: Nick Menzi · Status: lokaler, fiktiver No-Send-Demonstrator", size=9.2))
    y -= 18
    rule(c, y)
    y -= 24
    y = heading(c, y, "Ziel", level=2)
    y = wrapped(c, LEFT, y, "Docker-ausführbarer Hermes-Demonstrator für das kontrollierte Erstellen und Prüfen fiktiver E-Mail-Entwürfe der Onlineshop Demo AG. Das Projekt ist absichtlich kein Newsletter- oder Versandsystem.")
    y -= 8
    y = heading(c, y, "Ergebnis", level=2)
    items = [
        "Versioniertes Agentenprofil und gezielte Übernahme in eine isolierte lokale Runtime.",
        "Eine kanonische, fiktive 3R-Kontaktquelle: 50 Kontakte – 17 recruit, 17 retain, 16 recover.",
        "Deterministische kontaktbezogene Review-Queue mit Vor/Zurück, lokalem Prüfen, Bestätigen, Überspringen und Abbruch.",
        "Review-Ansicht ohne E-Mail-Adresse; kein SMTP, CRM, Webhook, Versand oder automatischer Export.",
    ]
    for item in items:
        y = wrapped(c, LEFT + 10, y, "• " + item, width=84)
        y -= 3
    y -= 2
    box(c, LEFT, 106, 503, 105, "Sicherer Standardzustand", "Jeder Queue-Eintrag bleibt draft_only und no_send. Ein bestätigter Entwurf ist weder versandt noch zugestellt. Reale Kontakt- oder Kundendaten sind nicht Teil dieser Demo.", accent=True)
    footer(c, 1)
    return b"".join(c)


def page_two() -> bytes:
    c: list[bytes] = []
    y = TOP
    y = heading(c, y, "Architektur und kontrollierter Workflow", level=1)
    c.append(text_command(LEFT, y, "Die freie TUI-Unterhaltung unterstützt Formulierungen. Für Empfängerauswahl und Reihenfolge gilt die lokale Review-Queue.", size=9.2))
    x = 171
    box(c, x, 650, 254, 60, "1. Anfrage erfassen", "Ziel, Dienstleistung, Ton und 3R-Zielgruppe klären.", accent=True)
    arrow(c, x + 127, 650, 625)
    box(c, x, 565, 254, 60, "2. Empfänger binden", "Kanonische CSV liefert Gruppe und exakte Kontaktanzahl.")
    arrow(c, x + 127, 565, 540)
    box(c, x, 480, 254, 60, "3. Review-Queue starten", "Entwurf n von Gesamtzahl; aktueller fiktiver Kontakt ohne Adresse.", accent=True)
    arrow(c, x + 127, 480, 455)
    box(c, x, 395, 254, 60, "4. Entwurf prüfen", "Text lokal erfassen oder überarbeiten; Änderungen bleiben am Queue-Element.")
    arrow(c, x + 127, 395, 370)
    box(c, x, 310, 254, 60, "5. Entscheiden", "Bestätigen, überspringen, vorheriger/nächster Kontakt oder Abbruch.", accent=True)
    arrow(c, x + 127, 310, 285)
    box(c, x, 225, 254, 60, "6. Export erst später", "Nur nach vollständiger menschlicher Prüfung und separater Freigabe.")
    box(c, 46, 103, 503, 76, "Was bewusst fehlt", "Kein Versandadapter, kein SMTP, kein CRM, kein Newsletter-Job und kein Messaging-Gateway. Die Queue führt nur lokale Entwurfs- und Prüfzustände.", accent=True)
    footer(c, 2)
    return b"".join(c)


def page_three() -> bytes:
    c: list[bytes] = []
    y = TOP
    y = heading(c, y, "Daten- und Sicherheitsgrenzen", level=1)
    y = heading(c, y, "Fiktive Datenbasis", level=2)
    y = wrapped(c, LEFT, y, "Die sichtbare Demoquelle data/demo_contacts_3r.csv enthält ausschließlich mit fictional_demo_only markierte Kontakte. Jede Adresse endet auf @example.invalid. Die technische Fixture unter tests/fixtures/ ist getrennt und keine zweite sichtbare Demoquelle.")
    y -= 10
    y = heading(c, y, "Minimierung in der Review-Queue", level=2)
    box(c, LEFT, 487, 238, 138, "Verwendete Anzeige-Felder", "Kontakt-ID, Vor- und Nachname, Firma, Sprache, 3R-Kategorie, Lifecycle-Status, Interesse und Tags.", accent=True)
    box(c, 311, 487, 238, 138, "Ausgeschlossen", "E-Mail-Adresse, interne Notizen, Zugangsdaten, reale Kundendaten und jede Versand- oder Zustellinformation.")
    y = 448
    y = heading(c, y, "Nachweisbare Grenzen", level=2)
    statements = [
        "Der Modellendpunkt wird nicht durch dieses Repository bereitgestellt oder bestätigt.",
        "Ein Live-Modellaufruf war kein Bestandteil der aktuellen Verifikation.",
        "Der reale Docker-TUI-Start erfolgt am berechtigten Host; in der Automationsumgebung war der Docker-Socket nicht verfügbar.",
        "Ein Kontakt in der CSV bedeutet keine Versandberechtigung – die Demo hat keinen Sender.",
    ]
    for item in statements:
        y = wrapped(c, LEFT + 10, y, "• " + item, width=84)
        y -= 3
    box(c, LEFT, 118, 503, 84, "Kernprinzip", "Eine plausible Modellantwort wird nie als Firmenfakt behandelt. Angebote, Rabatte, Fristen, Lieferzeiten oder Kundeneigenschaften müssen aus der Bedienereingabe stammen oder ausdrücklich als Vorschlag gekennzeichnet sein.", accent=True)
    footer(c, 3)
    return b"".join(c)


def page_four() -> bytes:
    c: list[bytes] = []
    y = TOP
    y = heading(c, y, "Verifikation, Reproduzierbarkeit und nächster Schritt", level=1)
    box(c, LEFT, 640, 503, 78, "Verifizierter Stand", "43/43 Offline-Tests bestanden: CSV-Struktur und 3R-Zahlen, Datenminimierung, No-Send-Status, Queue-Navigation, lokale Entwurfsbestätigung, Profilübernahme, Plugin-Import sowie Docker-Compose-Konfiguration.", accent=True)
    y = 608
    y = heading(c, y, "Reproduzierbarer Ablauf", level=2)
    steps = [
        "make test – Offline-Prüfungen ohne Modellaufruf ausführen.",
        "make profile-apply – versioniertes Profil kontrolliert in die lokale Runtime übernehmen.",
        "sudo make run – Hermes-TUI am berechtigten Host starten.",
        "Fiktive 3R-Gruppe ansehen und eine kontaktbezogene Review-Queue starten.",
    ]
    for number, step in enumerate(steps, start=1):
        y = wrapped(c, LEFT + 10, y, f"{number}. {step}", width=84)
        y -= 3
    y -= 4
    y = heading(c, y, "Offene Grenze", level=2)
    y = wrapped(c, LEFT, y, "Die natürliche Modellunterhaltung kann außerhalb des kontrollierten Queue-Pfads weiterhin unpassende Geschäftsdetails formulieren. Darum ersetzt die Review-Queue keine Zukunftsarbeit an der TUI, sondern sichert bereits Empfängerauswahl, Reihenfolge und lokalen Review-Status ab.")
    y -= 10
    y = heading(c, y, "Nächster sinnvoller Ausbau", level=2)
    y = wrapped(c, LEFT, y, "Die Queue direkt in den normalen TUI-Dialog einbetten: Vor jedem konkreten Entwurf zuerst Empfängergruppe aus der CSV binden, die exakte Zahl nennen und dann den aktuellen Review-Kontakt verwenden. Reale Datenimporte, Versand, CRM und Messaging bleiben außerhalb dieses Demonstrators.")
    box(c, LEFT, 107, 503, 83, "Entscheidungsvorlage", "Für die Hackathon-Demo ist der Stand nachvollziehbar und sicher begrenzt. Für eine produktive Lösung wären reale Consent-/Suppression-Prüfungen, authentifizierte Rollen, ein gesondert autorisierter Versandadapter und eine neue Datenschutz- und Sicherheitsfreigabe erforderlich.", accent=True)
    footer(c, 4)
    return b"".join(c)


def page_one_en() -> bytes:
    c: list[bytes] = []
    y = TOP
    c.append(b"0.05 0.19 0.34 rg\n")
    c.append(text_command(LEFT, y, OFFICIAL_PROJECT_NAME, size=14, font="F2"))
    c.append(b"0 g\n")
    y -= 25
    c.append(text_command(LEFT, y, "Technical brief · Hack Apertus Online Hackathon · Track 2B", size=10, font="F2"))
    y -= 16
    c.append(text_command(LEFT, y, "Project: Nick Menzi · Status: local fictional no-send demonstrator", size=9.2))
    y -= 18
    rule(c, y)
    y -= 24
    y = heading(c, y, "Purpose", level=2)
    y = wrapped(c, LEFT, y, "A Docker-runnable Hermes demonstrator for controlled creation and review of fictional email drafts for Onlineshop Demo AG. The project is deliberately not a newsletter or email-delivery system.")
    y -= 8
    y = heading(c, y, "Result", level=2)
    for item in [
        "Versioned agent profile and controlled transfer to an isolated local runtime.",
        "One canonical fictional 3R contact source: 50 contacts – 17 recruit, 17 retain, 16 recover.",
        "Deterministic per-contact review queue with previous/next, local review, confirmation, skip and abort.",
        "No email address in the review view; no SMTP, CRM, webhook, sending or automatic export.",
    ]:
        y = wrapped(c, LEFT + 10, y, "• " + item, width=84)
        y -= 3
    box(c, LEFT, 106, 503, 105, "Safe default state", "Every queue item remains draft_only and no_send. A confirmed draft is neither sent nor delivered. No real contact or customer data is part of this demo.", accent=True)
    footer(c, 1, language="en")
    return b"".join(c)


def page_two_en() -> bytes:
    c: list[bytes] = []
    y = TOP
    y = heading(c, y, "Architecture and controlled workflow", level=1)
    c.append(text_command(LEFT, y, "Free TUI conversation supports drafting. The local review queue controls recipient selection and order.", size=9.2))
    x = 171
    steps = [
        (650, "1. Capture request", "Clarify goal, service, tone and 3R target group."),
        (565, "2. Bind recipients", "Canonical CSV supplies the group and exact contact count."),
        (480, "3. Start review queue", "Draft n of total; current fictional contact without address."),
        (395, "4. Review draft", "Capture or revise text locally; changes stay with the queue item."),
        (310, "5. Decide", "Confirm, skip, previous/next contact or abort."),
        (225, "6. Export later", "Only after full human review and separate approval."),
    ]
    for index, (box_y, title, body) in enumerate(steps):
        box(c, x, box_y, 254, 60, title, body, accent=index % 2 == 0)
        if index < len(steps) - 1:
            arrow(c, x + 127, box_y, box_y - 25)
    box(c, 46, 103, 503, 76, "What is intentionally absent", "No sending adapter, SMTP, CRM, newsletter job or messaging gateway. The queue only manages local draft and review states.", accent=True)
    footer(c, 2, language="en")
    return b"".join(c)


def page_three_en() -> bytes:
    c: list[bytes] = []
    y = TOP
    y = heading(c, y, "Data and safety boundaries", level=1)
    y = heading(c, y, "Fictional data basis", level=2)
    y = wrapped(c, LEFT, y, "The visible source data/demo_contacts_3r.csv contains only contacts marked fictional_demo_only. Every address ends in @example.invalid. The technical fixture under tests/fixtures/ is separate and is not a second visible demo source.")
    y -= 10
    y = heading(c, y, "Review-queue minimisation", level=2)
    box(c, LEFT, 487, 238, 138, "Displayed fields", "Contact ID, first and last name, company, language, 3R category, lifecycle stage, interest and tags.", accent=True)
    box(c, 311, 487, 238, 138, "Excluded", "Email address, internal notes, credentials, real customer data and any sending or delivery information.")
    y = 448
    y = heading(c, y, "Evidence-based limits", level=2)
    for item in [
        "The model endpoint is not supplied or verified by this repository.",
        "A live model call was not part of the current verification.",
        "The real Docker TUI must run on an authorised host; the Docker socket was unavailable in the automation environment.",
        "A contact in the CSV does not grant delivery permission – the demo has no sender.",
    ]:
        y = wrapped(c, LEFT + 10, y, "• " + item, width=84)
        y -= 3
    box(c, LEFT, 118, 503, 84, "Core principle", "A plausible model response is never treated as a company fact. Offers, discounts, deadlines, delivery times or customer attributes must come from operator input or be explicitly labelled as a suggestion.", accent=True)
    footer(c, 3, language="en")
    return b"".join(c)


def page_four_en() -> bytes:
    c: list[bytes] = []
    y = TOP
    y = heading(c, y, "Verification, reproducibility and next step", level=1)
    box(c, LEFT, 640, 503, 78, "Verified status", "43/43 offline tests passed: CSV structure and 3R counts, data minimisation, no-send state, queue navigation, local draft confirmation, profile application, plugin import and Docker Compose configuration.", accent=True)
    y = 608
    y = heading(c, y, "Reproducible sequence", level=2)
    for number, step in enumerate([
        "make test – run offline checks without a model call.",
        "make profile-apply – transfer the versioned profile to the local runtime.",
        "sudo make run – start the Hermes TUI on the authorised host.",
        "View a fictional 3R group and start a per-contact review queue.",
    ], start=1):
        y = wrapped(c, LEFT + 10, y, f"{number}. {step}", width=84)
        y -= 3
    y -= 4
    y = heading(c, y, "Open limitation", level=2)
    y = wrapped(c, LEFT, y, "Outside the controlled queue path, natural model conversation can still formulate unsuitable business details. The review queue therefore does not replace further TUI work; it already safeguards recipient selection, ordering and local review state.")
    y -= 10
    y = heading(c, y, "Next useful increment", level=2)
    y = wrapped(c, LEFT, y, "Embed the queue directly in the normal TUI dialog: before every concrete draft, bind the recipient group from the CSV, state the exact count and then use the current review contact. Real data imports, sending, CRM and messaging remain outside this demonstrator.")
    box(c, LEFT, 107, 503, 83, "Decision statement", "The Hackathon demo is traceable and safely bounded. A production solution would require real consent and suppression checks, authenticated roles, a separately authorised sending adapter, and new privacy and security approval.", accent=True)
    footer(c, 4, language="en")
    return b"".join(c)


def build_pdf(streams: list[bytes]) -> bytes:
    objects: list[bytes] = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"",  # Pages tree, completed after page objects are numbered.
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica /Encoding /WinAnsiEncoding >>",
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica-Bold /Encoding /WinAnsiEncoding >>",
    ]
    page_numbers: list[int] = []
    for stream in streams:
        page_number = len(objects) + 1
        content_number = page_number + 1
        page_numbers.append(page_number)
        objects.append(
            f"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 {PAGE_WIDTH} {PAGE_HEIGHT}] /Resources << /Font << /F1 3 0 R /F2 4 0 R >> >> /Contents {content_number} 0 R >>".encode("ascii")
        )
        objects.append(f"<< /Length {len(stream)} >>\nstream\n".encode("ascii") + stream + b"endstream")
    kids = " ".join(f"{number} 0 R" for number in page_numbers)
    objects[1] = f"<< /Type /Pages /Kids [{kids}] /Count {len(page_numbers)} >>".encode("ascii")

    output = bytearray(b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n")
    offsets = [0]
    for number, body in enumerate(objects, start=1):
        offsets.append(len(output))
        output.extend(f"{number} 0 obj\n".encode("ascii"))
        output.extend(body)
        output.extend(b"\nendobj\n")
    xref = len(output)
    output.extend(f"xref\n0 {len(objects) + 1}\n".encode("ascii"))
    output.extend(b"0000000000 65535 f\n")
    for offset in offsets[1:]:
        output.extend(f"{offset:010d} 00000 n\n".encode("ascii"))
    output.extend(f"trailer\n<< /Size {len(objects) + 1} /Root 1 0 R >>\nstartxref\n{xref}\n%%EOF\n".encode("ascii"))
    return bytes(output)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--language", choices=("de", "en"), default="de")
    parser.add_argument("input", type=Path, help="Markdown source retained beside the PDF")
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    if not args.input.is_file():
        raise SystemExit(f"missing report source: {args.input}")
    pages = [page_one(), page_two(), page_three(), page_four()]
    if args.language == "en":
        pages = [page_one_en(), page_two_en(), page_three_en(), page_four_en()]
    args.output.write_bytes(build_pdf(pages))
    print(f"created {args.output} with 4 page(s) [{args.language}]")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
