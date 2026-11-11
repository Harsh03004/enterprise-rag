"""Generate the Orion product specification PDF used by the evaluation corpus.

The PDF is committed to the repository; rerun this script only when its content
needs to change:

    uv run python evaluation/build_corpus_pdf.py

Tables are drawn with ruled cell borders so PyMuPDF table detection exercises
the same path as real-world specification sheets.
"""

from __future__ import annotations

from pathlib import Path

import fitz

OUTPUT = Path(__file__).parent / "corpus" / "orion_thermostat_spec.pdf"

PAGE_WIDTH, PAGE_HEIGHT = fitz.paper_size("a4")
MARGIN = 56
FONT = "helv"
BOLD = "hebo"


class Writer:
    def __init__(self, document: fitz.Document) -> None:
        self.document = document
        self.page = document.new_page(width=PAGE_WIDTH, height=PAGE_HEIGHT)
        self.y = MARGIN

    def new_page(self) -> None:
        self.page = self.document.new_page(width=PAGE_WIDTH, height=PAGE_HEIGHT)
        self.y = MARGIN

    def heading(self, text: str, size: float = 14) -> None:
        self.y += 6
        self.page.insert_text((MARGIN, self.y + size), text, fontname=BOLD, fontsize=size)
        self.y += size + 10

    def paragraph(self, text: str, size: float = 10.5) -> None:
        rect = fitz.Rect(MARGIN, self.y, PAGE_WIDTH - MARGIN, PAGE_HEIGHT - MARGIN)
        remaining = self.page.insert_textbox(rect, text, fontname=FONT, fontsize=size)
        used = rect.height - remaining
        self.y += used + 8

    def table(self, rows: list[list[str]], widths: list[float], size: float = 9.5) -> None:
        row_height = size * 2.4
        for row_index, row in enumerate(rows):
            x = MARGIN
            for cell, width in zip(row, widths, strict=True):
                rect = fitz.Rect(x, self.y, x + width, self.y + row_height)
                self.page.draw_rect(rect, color=(0, 0, 0), width=0.6)
                self.page.insert_textbox(
                    fitz.Rect(rect.x0 + 4, rect.y0 + 5, rect.x1 - 4, rect.y1),
                    cell,
                    fontname=BOLD if row_index == 0 else FONT,
                    fontsize=size,
                )
                x += width
            self.y += row_height
        self.y += 14


def build() -> None:
    document = fitz.open()
    document.set_metadata({"title": "Orion Smart Thermostat Specification", "author": "Orion Home Devices"})
    writer = Writer(document)

    writer.heading("Orion Smart Thermostat - Product Specification", 16)
    writer.paragraph(
        "Orion Home Devices released the Orion X2 smart thermostat in March 2026. "
        "The X2 replaces the Orion X1, which was released in 2023 and is no longer "
        "sold. This document compares the two generations and describes the Orion "
        "Cloud subscription plans."
    )

    writer.heading("1. Hardware comparison")
    writer.table(
        [
            ["Specification", "Orion X2 (2026)", "Orion X1 (2023)"],
            ["Price at launch", "179 USD", "129 USD"],
            ["Battery life", "18 months", "12 months"],
            ["Temperature accuracy", "+/- 0.2 C", "+/- 0.5 C"],
            ["Wireless", "Wi-Fi 6 and Thread", "Wi-Fi 4"],
            ["Matter support", "Yes", "No"],
            ["Display", "2.8 inch colour", "2.1 inch monochrome"],
            ["Warranty", "3 years", "2 years"],
        ],
        [170, 160, 150],
    )

    writer.heading("2. Installation")
    writer.paragraph(
        "The Orion X1 required a common wire (C-wire) for continuous power. The "
        "Orion X2 does not require a C-wire: every X2 ships with a power extender "
        "kit for homes without one. Professional installation is optional; most "
        "customers complete installation in about 30 minutes using the Orion app."
    )
    writer.paragraph(
        "The X2 supports 24 V heating and cooling systems, including heat pumps "
        "with up to two auxiliary stages. It does not support line-voltage "
        "(120 V or 240 V) electric baseboard heaters."
    )

    writer.new_page()
    writer.heading("3. Orion Cloud subscription plans")
    writer.paragraph(
        "Every Orion thermostat works without a subscription. Orion Cloud plans "
        "add remote features. Prices are per home, billed monthly."
    )
    writer.table(
        [
            ["Plan", "Monthly price", "History retention", "Energy reports", "Homes"],
            ["Basic", "Free", "7 days", "No", "1"],
            ["Plus", "3.99 USD", "90 days", "Monthly", "Up to 3"],
            ["Pro", "8.99 USD", "2 years", "Weekly", "Up to 10"],
        ],
        [80, 95, 105, 105, 95],
    )

    writer.heading("4. Software support")
    writer.paragraph(
        "Orion provides security and firmware updates for at least 5 years after "
        "a model's release date. Firmware updates install automatically between "
        "02:00 and 04:00 local time unless the owner postpones them in the app. "
        "Support for the Orion X1 ends in 2028."
    )

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    document.save(OUTPUT, garbage=4, deflate=True)
    document.close()


if __name__ == "__main__":
    build()
    print(f"Wrote {OUTPUT}")
