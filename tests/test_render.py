"""Rendering Markdown to a branded PDF (F6, F13), checked through the extracted text."""

import io
from pathlib import Path
from typing import Any

import pdfplumber
import pytest
import reportlab

from brandpdf import render
from brandpdf.brand import Brand, parse_brand

VERA = Path(reportlab.__file__).parent / "fonts"

SAMPLE = """\
# Site Safety Checklist

Read this before your first visit. **Bold** and *italic* words keep their style.

## Before you start

- Read the induction notes
- Sign in at reception
  - Collect a visitor badge
- Park in the visitor bays

## On site

1. Wear safety boots
2. Report hazards to the duty manager

### Contacts

Call the duty manager & ask for <help>.
"""

ORDER = [
    "Site Safety Checklist",
    "Read this before your first visit.",
    "Before you start",
    "Read the induction notes",
    "Sign in at reception",
    "Collect a visitor badge",
    "Park in the visitor bays",
    "On site",
    "Wear safety boots",
    "Report hazards to the duty manager",
    "Contacts",
    "Call the duty manager & ask for <help>.",
]


def make_brand(**overrides: Any) -> Brand:
    data: dict[str, Any] = {
        "name": "Fernleaf Studio",
        "colors": {
            "primary": "#2E5E4E",
            "secondary": "#8FB9A8",
            "accent": "#F4A259",
            "text": "#222222",
        },
        "fonts": {"heading": str(VERA / "VeraBd.ttf"), "body": str(VERA / "Vera.ttf")},
    }
    data.update(overrides)
    return parse_brand(data)


@pytest.fixture(scope="module")
def pdf() -> pdfplumber.PDF:
    return pdfplumber.open(io.BytesIO(render(SAMPLE, make_brand())))


def full_text(document: pdfplumber.PDF) -> str:
    return "\n".join(page.extract_text() for page in document.pages)


def chars_of(document: pdfplumber.PDF, phrase: str) -> list[dict[str, Any]]:
    """The characters that spell the first occurrence of ``phrase`` on any page."""
    for page in document.pages:
        chars = [c for c in page.chars if c["text"].strip()]
        letters = "".join(c["text"] for c in chars)
        target = phrase.replace(" ", "")
        start = letters.find(target)
        if start != -1:
            return chars[start : start + len(target)]
    raise AssertionError(f"{phrase!r} not found in the PDF")


def rgb(hex_colour: str) -> tuple[float, float, float]:
    return tuple(int(hex_colour[i : i + 2], 16) / 255 for i in (1, 3, 5))  # type: ignore[return-value]


def assert_colour(char: dict[str, Any], hex_colour: str) -> None:
    assert char["non_stroking_color"] == pytest.approx(rgb(hex_colour), abs=0.01)


def test_output_is_a_pdf() -> None:
    assert render(SAMPLE, make_brand()).startswith(b"%PDF-")


def test_every_heading_and_list_item_appears_in_order(pdf: pdfplumber.PDF) -> None:
    text = full_text(pdf)

    positions = [text.find(phrase) for phrase in ORDER]

    assert -1 not in positions, [p for p, i in zip(ORDER, positions, strict=True) if i == -1]
    assert positions == sorted(positions)


def test_lists_have_bullets_and_numbers(pdf: pdfplumber.PDF) -> None:
    lines = full_text(pdf).splitlines()

    assert any(line.startswith("•") and "Read the induction notes" in line for line in lines)
    assert any(line.startswith("1.") and "Wear safety boots" in line for line in lines)
    assert any(line.startswith("2.") and "Report hazards" in line for line in lines)


def test_headings_use_the_heading_font_and_primary_colour(pdf: pdfplumber.PDF) -> None:
    for heading in ("Site Safety Checklist", "Before you start", "Contacts"):
        chars = chars_of(pdf, heading)
        assert all(c["fontname"].endswith("BitstreamVeraSans-Bold") for c in chars)
        assert_colour(chars[0], "#2E5E4E")


def test_headings_shrink_by_level(pdf: pdfplumber.PDF) -> None:
    h1, h2, h3 = (
        chars_of(pdf, text)[0]["size"]
        for text in ("Site Safety Checklist", "Before you start", "Contacts")
    )
    body = chars_of(pdf, "Read this before")[0]["size"]

    assert h1 > h2 > h3 > body


def test_body_uses_the_body_font_and_text_colour(pdf: pdfplumber.PDF) -> None:
    chars = chars_of(pdf, "Read this before your first visit.")

    assert all(c["fontname"].endswith("BitstreamVeraSans-Roman") for c in chars)
    assert_colour(chars[0], "#222222")


def test_bullets_use_the_accent_colour(pdf: pdfplumber.PDF) -> None:
    bullet = next(c for c in pdf.pages[0].chars if c["text"] == "•")

    assert_colour(bullet, "#F4A259")


def test_bold_and_italic_with_built_in_fonts() -> None:
    brand = make_brand(fonts={"heading": "Times-Bold", "body": "Helvetica"})
    document = pdfplumber.open(io.BytesIO(render(SAMPLE, brand)))

    assert chars_of(document, "Site Safety Checklist")[0]["fontname"] == "Times-Bold"
    assert chars_of(document, "Read this")[0]["fontname"] == "Helvetica"
    assert chars_of(document, "Bold")[0]["fontname"] == "Helvetica-Bold"
    assert chars_of(document, "italic")[0]["fontname"] == "Helvetica-Oblique"


def test_page_size_and_margins_follow_the_brand() -> None:
    brand = make_brand(
        page={"size": "Letter", "margins_mm": {"top": 50, "left": 40, "right": 15, "bottom": 20}}
    )
    document = pdfplumber.open(io.BytesIO(render(SAMPLE, brand)))
    page = document.pages[0]
    title = chars_of(document, "Site Safety Checklist")[0]

    assert (page.width, page.height) == (612, 792)
    assert title["x0"] == pytest.approx(40 * 72 / 25.4, abs=1)
    assert 50 * 72 / 25.4 <= title["top"] < 50 * 72 / 25.4 + title["size"]


def test_long_document_flows_onto_more_pages() -> None:
    markdown = "# Report\n\n" + "\n\n".join(f"Paragraph number {n}." for n in range(1, 121))

    document = pdfplumber.open(io.BytesIO(render(markdown, make_brand())))

    assert len(document.pages) > 1
    assert "Paragraph number 120." in document.pages[-1].extract_text()


def test_title_metadata_comes_from_the_first_heading(pdf: pdfplumber.PDF) -> None:
    assert pdf.metadata["Title"] == "Site Safety Checklist"
    assert pdf.metadata["Author"] == "Fernleaf Studio"


def test_title_falls_back_to_the_brand_name() -> None:
    document = pdfplumber.open(io.BytesIO(render("Just a paragraph.", make_brand())))

    assert document.metadata["Title"] == "Fernleaf Studio"


def test_empty_document_renders_one_blank_page() -> None:
    document = pdfplumber.open(io.BytesIO(render("", make_brand())))

    assert len(document.pages) == 1
    assert document.pages[0].extract_text().splitlines() == ["Fernleaf Studio", "Page 1 of 1"]


def test_same_inputs_give_identical_bytes() -> None:
    assert render(SAMPLE, make_brand()) == render(SAMPLE, make_brand())


def test_code_block_and_rule_render() -> None:
    markdown = "Before\n\n```\nbrandpdf build doc.md\n```\n\n---\n\nAfter"
    document = pdfplumber.open(io.BytesIO(render(markdown, make_brand())))
    page = document.pages[0]

    assert "brandpdf build doc.md" in page.extract_text()
    assert chars_of(document, "brandpdf")[0]["fontname"] == "Courier"
    assert page.lines or page.rects  # the horizontal rule
