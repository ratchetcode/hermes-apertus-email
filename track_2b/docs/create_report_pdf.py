#!/usr/bin/env python3
"""Create a portable text PDF from the technical-report Markdown without extras."""

from __future__ import annotations

import argparse
import re
import textwrap
from pathlib import Path

PAGE_WIDTH = 595
PAGE_HEIGHT = 842
MARGIN = 48
LEADING = 13
LINES_PER_PAGE = 51


def pdf_escape(text: str) -> str:
    return text.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")


def report_lines(markdown: str) -> list[str]:
    lines: list[str] = []
    for raw_line in markdown.splitlines():
        line = raw_line.strip()
        if not line:
            lines.append("")
            continue
        line = re.sub(r"^#{1,6}\s*", "", line)
        line = re.sub(r"^[-*]\s+", "- ", line)
        line = line.replace("`", "").replace("**", "")
        line = line.replace("|", " / ")
        wrapped = textwrap.wrap(line, width=92, break_long_words=False) or [""]
        lines.extend(wrapped)
    return lines


def page_stream(lines: list[str], page_number: int) -> bytes:
    commands = [
        "BT",
        "/F1 9 Tf",
        f"{MARGIN} {PAGE_HEIGHT - MARGIN} Td",
        f"(Apertus Draft Gate - Technical Report - Page {page_number}) Tj",
        f"0 -{LEADING * 2} Td",
    ]
    for line in lines:
        safe = line.encode("ascii", "replace").decode("ascii")
        commands.append(f"({pdf_escape(safe)}) Tj")
        commands.append(f"0 -{LEADING} Td")
    commands.append("ET")
    return "\n".join(commands).encode("ascii")


def build_pdf(pages: list[list[str]]) -> bytes:
    objects: list[bytes] = []
    page_object_numbers: list[int] = []

    # Reserve catalog, pages tree and font. Every page gets page + content objects.
    objects.extend([b"", b"", b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>"])
    for index, lines in enumerate(pages, start=1):
        page_number = 4 + (index - 1) * 2
        content_number = page_number + 1
        page_object_numbers.append(page_number)
        stream = page_stream(lines, index)
        objects.append(
            f"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 {PAGE_WIDTH} {PAGE_HEIGHT}] "
            f"/Resources << /Font << /F1 3 0 R >> >> /Contents {content_number} 0 R >>".encode("ascii")
        )
        objects.append(
            f"<< /Length {len(stream)} >>\nstream\n".encode("ascii")
            + stream
            + b"\nendstream"
        )

    objects[0] = b"<< /Type /Catalog /Pages 2 0 R >>"
    kids = " ".join(f"{number} 0 R" for number in page_object_numbers)
    objects[1] = f"<< /Type /Pages /Kids [{kids}] /Count {len(page_object_numbers)} >>".encode("ascii")

    output = bytearray(b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n")
    offsets = [0]
    for object_number, object_body in enumerate(objects, start=1):
        offsets.append(len(output))
        output.extend(f"{object_number} 0 obj\n".encode("ascii"))
        output.extend(object_body)
        output.extend(b"\nendobj\n")
    xref_offset = len(output)
    output.extend(f"xref\n0 {len(objects) + 1}\n".encode("ascii"))
    output.extend(b"0000000000 65535 f\n")
    for offset in offsets[1:]:
        output.extend(f"{offset:010d} 00000 n\n".encode("ascii"))
    output.extend(
        f"trailer\n<< /Size {len(objects) + 1} /Root 1 0 R >>\nstartxref\n{xref_offset}\n%%EOF\n".encode("ascii")
    )
    return bytes(output)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("input", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()

    lines = report_lines(args.input.read_text(encoding="utf-8"))
    pages = [lines[index:index + LINES_PER_PAGE] for index in range(0, len(lines), LINES_PER_PAGE)]
    args.output.write_bytes(build_pdf(pages))
    print(f"created {args.output} with {len(pages)} page(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
