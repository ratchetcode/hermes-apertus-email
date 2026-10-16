#!/usr/bin/env python3
"""Build a compact four-page PDF report for Apertus Draft Gate.

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


def escape_pdf(text: str) -> bytes:
    raw = text.encode("latin-1", "replace")
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


def footer(commands: list[bytes], page: int) -> None:
    rule(commands, 37)
    commands.append(text_command(LEFT, 22, "Apertus Draft Gate · Technischer Kurzbericht · 15. Oktober 2026", size=7.5))
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
    y = heading(c, y, "Apertus Draft Gate", level=1)
    c.append(text_command(LEFT, y, "Technischer Kurzbericht · Hack Apertus Online Hackathon · Track 2B", size=10, font="F2"))
    y -= 18
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
    box(c, LEFT, 640, 503, 78, "Verifizierter Stand", "42/42 Offline-Tests bestanden: CSV-Struktur und 3R-Zahlen, Datenminimierung, No-Send-Status, Queue-Navigation, lokale Entwurfsbestätigung, Profilübernahme, Plugin-Import sowie Docker-Compose-Konfiguration.", accent=True)
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
    parser.add_argument("input", type=Path, help="Markdown source retained beside the PDF")
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    if not args.input.is_file():
        raise SystemExit(f"missing report source: {args.input}")
    args.output.write_bytes(build_pdf([page_one(), page_two(), page_three(), page_four()]))
    print(f"created {args.output} with 4 page(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
