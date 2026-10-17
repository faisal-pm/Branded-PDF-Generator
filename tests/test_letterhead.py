"""Generated and background letterheads, page numbers (F3, F4, F5, F10)."""

from pathlib import Path

import pytest
from helpers import (
    assert_colour,
    assert_matches_snapshot,
    chars_of,
    find_chars,
    make_brand,
    mm,
    open_pdf,
    write_letterhead_pdf,
    write_letterhead_png,
    write_logo,
)

from brandpdf import render

THREE_PAGES = "# Quarterly Site Report\n\n" + "\n\n".join(
    f"## Section {n}\n\n" + " ".join(["Site works continued as planned this week."] * 12)
    for n in range(1, 13)
)


@pytest.fixture(scope="module")
def generated() -> bytes:
    return render(THREE_PAGES, make_brand())


@pytest.fixture
def assets(tmp_path: Path) -> Path:
    write_letterhead_pdf(tmp_path / "first.pdf", "FERNLEAF FIRST PAGE")
    write_letterhead_pdf(tmp_path / "later.pdf", "FERNLEAF CONTINUATION")
    write_letterhead_png(tmp_path / "letterhead.png")
    write_logo(tmp_path / "logo.png")
    return tmp_path


def test_sample_runs_to_three_pages(generated: bytes) -> None:
    assert len(open_pdf(generated).pages) == 3


# Generated letterhead (F4)


def test_every_page_is_numbered_page_x_of_y(generated: bytes) -> None:
    for number, page in enumerate(open_pdf(generated).pages, 1):
        assert f"Page {number} of 3" in page.extract_text()


def test_footer_carries_the_contact_line_on_every_page(generated: bytes) -> None:
    for page in open_pdf(generated).pages:
        assert "fernleaf.example · hello@fernleaf.example · +00 1234 5678" in page.extract_text()


def test_first_page_header_shows_the_name_and_contact_block(generated: bytes) -> None:
    page = open_pdf(generated).pages[0]
    text = page.extract_text()

    name = find_chars(page, "Fernleaf Studio")
    assert name is not None and name[0]["top"] < mm(30)
    assert_colour(name[0]["non_stroking_color"], "#2E5E4E")
    for line in ("12 Willow Lane", "Brookfield", "+00 1234 5678"):
        assert line in text


def test_first_page_has_a_primary_colour_band_across_the_top(generated: bytes) -> None:
    page = open_pdf(generated).pages[0]

    band = [r for r in page.rects if r["top"] < 1 and r["width"] >= page.width - 1]

    assert band
    assert_colour(band[0]["non_stroking_color"], "#2E5E4E")


def test_continuation_pages_show_a_compact_header_with_the_title(generated: bytes) -> None:
    for page in open_pdf(generated).pages[1:]:
        text = page.extract_text()
        header = [line for line in text.splitlines()][0]
        assert "Fernleaf Studio" in header
        assert "Quarterly Site Report" in header
        assert "12 Willow Lane" not in text


def test_body_text_clears_the_header_and_footer(generated: bytes) -> None:
    document = open_pdf(generated)
    first, second = document.pages[0], document.pages[1]

    title = find_chars(first, "Quarterly Site Report")
    assert title is not None and title[0]["top"] >= mm(36)
    body_on_page_two = [c for c in second.chars if c["size"] > 9]
    assert min(c["top"] for c in body_on_page_two) >= mm(20)
    for page in document.pages:
        body = [c for c in page.chars if c["size"] > 9]
        assert max(c["bottom"] for c in body) <= page.height - mm(20)


def test_logo_replaces_the_name_in_the_first_page_header(assets: Path) -> None:
    pdf = render(THREE_PAGES, make_brand(assets, logo="logo.png"))
    page = open_pdf(pdf).pages[0]

    logo = [image for image in page.images if image["top"] < mm(35)]
    assert len(logo) == 1
    assert find_chars(page, "Fernleaf Studio") is None


def test_document_without_contact_details_still_numbers_pages() -> None:
    pdf = render(THREE_PAGES, make_brand(contact={}))

    assert "Page 3 of 3" in open_pdf(pdf).pages[2].extract_text()


# Background letterheads (F3, F5)


def test_pdf_letterhead_on_first_page_and_continuation_on_the_rest(assets: Path) -> None:
    brand = make_brand(assets, letterhead={"first_page": "first.pdf", "continuation": "later.pdf"})

    pages = open_pdf(render(THREE_PAGES, brand)).pages

    assert "FERNLEAF FIRST PAGE" in pages[0].extract_text()
    assert "FERNLEAF CONTINUATION" not in pages[0].extract_text()
    for page in pages[1:]:
        assert "FERNLEAF CONTINUATION" in page.extract_text()
        assert "FERNLEAF FIRST PAGE" not in page.extract_text()


def test_first_page_letterhead_repeats_when_no_continuation_is_given(assets: Path) -> None:
    brand = make_brand(assets, letterhead={"first_page": "first.pdf"})

    for page in open_pdf(render(THREE_PAGES, brand)).pages:
        assert "FERNLEAF FIRST PAGE" in page.extract_text()


def test_pdf_letterhead_sits_under_the_content_and_keeps_page_numbers(assets: Path) -> None:
    brand = make_brand(assets, letterhead={"first_page": "first.pdf"})
    document = open_pdf(render(THREE_PAGES, brand))

    assert document.metadata["Title"] == "Quarterly Site Report"
    for number, page in enumerate(document.pages, 1):
        text = page.extract_text()
        assert f"Page {number} of 3" in text
        assert "hello@fernleaf.example" not in text  # no generated header or footer
    # the letterhead is drawn first, so its label precedes the body in the content stream
    first_page_text = document.pages[0].extract_text()
    assert first_page_text.index("FERNLEAF FIRST PAGE") < first_page_text.index("Section 1")


def test_pdf_letterhead_is_scaled_to_the_page(assets: Path) -> None:
    write_letterhead_pdf(assets / "letter-size.pdf", "LETTER SIZED", pagesize=(612, 792))
    brand = make_brand(assets, letterhead={"first_page": "letter-size.pdf"})

    page = open_pdf(render("# Short", brand)).pages[0]
    label = find_chars(page, "LETTER SIZED")

    assert (round(page.width), round(page.height)) == (595, 842)
    assert label is not None and label[-1]["x1"] < page.width


def test_png_letterhead_fills_every_page(assets: Path) -> None:
    brand = make_brand(assets, letterhead={"first_page": "letterhead.png"})

    for page in open_pdf(render(THREE_PAGES, brand)).pages:
        assert len(page.images) == 1
        image = page.images[0]
        assert (image["x0"], image["top"]) == pytest.approx((0, 0), abs=0.5)
        assert (image["width"], image["height"]) == pytest.approx((page.width, page.height), abs=1)


def test_background_colour_is_not_painted_over_a_letterhead(assets: Path) -> None:
    brand = make_brand(
        assets,
        colors={
            "primary": "#2E5E4E",
            "secondary": "#8FB9A8",
            "accent": "#F4A259",
            "background": "#FFF8EE",
        },
        letterhead={"first_page": "letterhead.png"},
    )

    page = open_pdf(render("# Short", brand)).pages[0]

    assert not [r for r in page.rects if r["width"] >= page.width - 1 and r["height"] > 800]


def test_background_colour_fills_generated_pages() -> None:
    brand = make_brand(
        colors={
            "primary": "#2E5E4E",
            "secondary": "#8FB9A8",
            "accent": "#F4A259",
            "background": "#FFF8EE",
        }
    )

    page = open_pdf(render("# Short", brand)).pages[0]
    fills = [r for r in page.rects if r["width"] >= page.width - 1 and r["height"] > 800]

    assert fills
    assert_colour(fills[0]["non_stroking_color"], "#FFF8EE")


def test_pdf_letterhead_output_is_deterministic(assets: Path) -> None:
    brand = make_brand(assets, letterhead={"first_page": "first.pdf", "continuation": "later.pdf"})

    assert render(THREE_PAGES, brand) == render(THREE_PAGES, brand)


def test_heading_colour_unchanged_by_letterhead(assets: Path) -> None:
    brand = make_brand(assets, letterhead={"first_page": "first.pdf"})

    title = chars_of(open_pdf(render(THREE_PAGES, brand)), "Quarterly Site Report")

    assert_colour(title[0]["non_stroking_color"], "#2E5E4E")


# Visual snapshots (milestone 4 check)


def test_snapshot_generated_letterhead(assets: Path) -> None:
    pdf = render(THREE_PAGES, make_brand(assets, logo="logo.png"))

    assert_matches_snapshot(pdf, "letterhead-generated")


def test_snapshot_background_letterheads(assets: Path) -> None:
    brand = make_brand(assets, letterhead={"first_page": "first.pdf", "continuation": "later.pdf"})

    assert_matches_snapshot(render(THREE_PAGES, brand), "letterhead-background")
