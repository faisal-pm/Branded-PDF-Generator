"""Tables, checklists, callouts, images and front matter (F6-F9, F11)."""

from pathlib import Path

import pytest
from helpers import (
    assert_colour,
    assert_matches_snapshot,
    chars_of,
    find_chars,
    make_brand,
    open_pdf,
    rgb,
    write_logo,
)
from PIL import Image

from brandpdf import render
from brandpdf.brand import BrandError
from brandpdf.errors import DocumentError

LONG_TABLE = "# Stock Take\n\n| Item | Location | Qty |\n|:--|:--|--:|\n" + "\n".join(
    f"| Item {n:02d} | Shed {n % 4 + 1} | {n * 3} |" for n in range(1, 61)
)

CHECKLIST = """\
# Before You Leave

- [x] Return the visitor badge
- [ ] Close the site gate
- [x] Sign out at reception
- [ ] Report any incidents
- [ ] Take your rubbish with you
"""

CALLOUTS = """\
> [!NOTE]
> The site office opens at 7am.

> [!TIP]
> Bring a water bottle.

> [!WARNING]
> Hard hats are required beyond the gate.

> A plain quote.
"""


def luminance(colour: tuple[float, ...]) -> float:
    red, green, blue = colour
    return 0.2126 * red + 0.7152 * green + 0.0722 * blue


def box_rects(page, size: float = 9.0) -> list[dict]:
    return [r for r in page.rects if abs(r["width"] - size) < 0.5 and abs(r["height"] - size) < 0.5]


# Tables (F6, F11)


def test_table_cells_render_in_reading_order() -> None:
    text = open_pdf(render(LONG_TABLE, make_brand())).pages[0].extract_text()

    assert "Item Location Qty" in text
    assert "Item 01 Shed 2 3" in text
    assert text.index("Item 01") < text.index("Item 02") < text.index("Item 03")


def test_long_table_repeats_its_header_on_every_page() -> None:
    document = open_pdf(render(LONG_TABLE, make_brand()))

    assert len(document.pages) >= 2
    assert "Item 60 Shed 1 180" in document.pages[-1].extract_text()
    for page in document.pages:
        header = find_chars(page, "Item Location Qty")
        assert header is not None, f"no header on page {page.page_number}"
        first_row = find_chars(page, "Shed")
        assert first_row is not None and header[0]["top"] < first_row[0]["top"]


def test_table_header_is_filled_with_the_primary_colour_and_readable_text() -> None:
    page = open_pdf(render(LONG_TABLE, make_brand())).pages[0]
    header = find_chars(page, "Location")

    assert header is not None
    fills = [
        r
        for r in page.rects
        if r["top"] <= header[0]["top"] <= r["bottom"] and r["fill"] and r["width"] > 20
    ]
    assert fills
    assert_colour(fills[0]["non_stroking_color"], "#2E5E4E")
    assert_colour(header[0]["non_stroking_color"], "#FFFFFF")


def test_light_primary_colour_gets_dark_header_text() -> None:
    brand = make_brand(
        colors={
            "primary": "#F2E8A0",
            "secondary": "#8FB9A8",
            "accent": "#F4A259",
            "text": "#222222",
        }
    )

    header = find_chars(open_pdf(render(LONG_TABLE, brand)).pages[0], "Location")

    assert header is not None
    assert_colour(header[0]["non_stroking_color"], "#222222")


def test_right_aligned_column_lines_up_on_the_right() -> None:
    words = open_pdf(render(LONG_TABLE, make_brand())).pages[0].extract_words()

    right_edges = {round(word["x1"]) for word in words if word["text"] in {"30", "60", "90"}}

    assert len(right_edges) == 1


# Checklists (F7)


def test_checklist_draws_ticked_and_unticked_boxes() -> None:
    page = open_pdf(render(CHECKLIST, make_brand())).pages[0]
    boxes = box_rects(page)
    ticked = [b for b in boxes if b["fill"]]
    unticked = [b for b in boxes if not b["fill"]]

    assert len(ticked) == 2
    assert len(unticked) == 3
    for box in boxes:
        assert_colour(box["stroking_color"], "#F4A259")
    assert_colour(ticked[0]["non_stroking_color"], "#F4A259")


def test_checklist_items_have_text_but_no_bullets() -> None:
    text = open_pdf(render(CHECKLIST, make_brand())).pages[0].extract_text()

    for item in ("Return the visitor badge", "Close the site gate", "Take your rubbish with you"):
        assert item in text
    assert "•" not in text
    assert "[x]" not in text and "[ ]" not in text


def test_each_box_sits_beside_its_item() -> None:
    page = open_pdf(render(CHECKLIST, make_brand())).pages[0]
    boxes = sorted(box_rects(page), key=lambda b: b["top"])
    labels = ["Return the visitor badge", "Close the site gate", "Sign out at reception"]

    for box, label in zip(boxes, labels, strict=False):
        chars = find_chars(page, label)
        assert chars is not None
        assert box["x1"] < chars[0]["x0"]
        assert abs(box["top"] - chars[0]["top"]) < 4


# Callouts and quotes (F8)


def test_callouts_show_a_label_and_a_bar_in_their_colour() -> None:
    document = open_pdf(render(CALLOUTS, make_brand()))
    page = document.pages[0]

    for label, colour in (("Note", "#2E5E4E"), ("Tip", "#8FB9A8"), ("Warning", "#F4A259")):
        label_chars = chars_of(document, label)
        bar = next(
            line
            for line in page.lines
            if line["top"] <= label_chars[0]["top"] <= line["bottom"] and line["x0"] < 80
        )
        assert_colour(bar["stroking_color"], colour)
        if label == "Note":  # dark enough to use as is
            assert_colour(label_chars[0]["non_stroking_color"], colour)
        else:  # pale brand colours are darkened so the label stays readable
            assert luminance(label_chars[0]["non_stroking_color"]) < luminance(rgb(colour))
    text = page.extract_text()
    assert "The site office opens at 7am." in text
    assert "[!NOTE]" not in text


def test_callouts_have_a_tinted_panel_and_a_coloured_bar() -> None:
    page = open_pdf(render(CALLOUTS, make_brand())).pages[0]
    body = find_chars(page, "Hard hats are required")
    assert body is not None

    around = [r for r in page.rects if r["top"] <= body[0]["top"] <= r["bottom"] and r["fill"]]
    panel = max(around, key=lambda r: r["width"])
    assert panel["width"] > 300
    assert tuple(panel["non_stroking_color"]) != (1, 1, 1)
    bars = [
        line
        for line in page.lines
        if line["x0"] <= panel["x0"] + 2 and line["top"] <= body[0]["top"] <= line["bottom"]
    ]
    assert bars
    assert_colour(bars[0]["stroking_color"], "#F4A259")


def test_plain_quote_has_a_rule_but_no_label() -> None:
    page = open_pdf(render(CALLOUTS, make_brand())).pages[0]
    quote = find_chars(page, "A plain quote.")

    assert quote is not None
    beside = [
        line
        for line in page.lines
        if line["x0"] < quote[0]["x0"] and line["top"] <= quote[0]["top"] <= line["bottom"]
    ]
    assert beside


# Images (F6)


def test_image_block_renders_scaled_to_the_page_width(tmp_path: Path) -> None:
    Image.new("RGB", (2000, 1000), "#8FB9A8").save(tmp_path / "map.png")

    page = open_pdf(render("![Site map](map.png)", make_brand(), base_dir=tmp_path)).pages[0]

    [image] = page.images
    assert image["x0"] == pytest.approx(20 * 72 / 25.4, abs=1)
    assert image["width"] == pytest.approx(page.width - 40 * 72 / 25.4, abs=1)
    assert image["height"] == pytest.approx(image["width"] / 2, abs=1)


def test_small_image_is_not_enlarged(tmp_path: Path) -> None:
    write_logo(tmp_path / "logo.png")  # 240 x 80 px

    [image] = open_pdf(render("![Logo](logo.png)", make_brand(), base_dir=tmp_path)).pages[0].images

    assert (image["width"], image["height"]) == pytest.approx((240 * 0.75, 80 * 0.75), abs=1)


@pytest.mark.parametrize(
    ("markdown", "expected"),
    [
        ("![Map](missing.png)", "image not found:"),
        ("![Map](https://example.org/map.png)", "remote images are not supported"),
        ("![Map](notes.txt)", "must be a .png, .jpg or .jpeg file"),
    ],
)
def test_bad_image_gives_a_readable_error(tmp_path: Path, markdown: str, expected: str) -> None:
    (tmp_path / "notes.txt").write_text("not an image")

    with pytest.raises(DocumentError) as excinfo:
        render(markdown, make_brand(), base_dir=tmp_path)

    assert expected in str(excinfo.value)


# Front matter (F9, F10)

FRONT_MATTER = """\
---
title: Site Safety Induction
subtitle: For contractors and visitors
date: 2026-10-17
reference: FS-SAF-001
---
## Welcome

Read every section before your first visit.
"""


def test_front_matter_renders_a_title_block() -> None:
    document = open_pdf(render(FRONT_MATTER, make_brand()))
    text = document.pages[0].extract_text()

    for line in (
        "Site Safety Induction",
        "For contractors and visitors",
        "2026-10-17",
        "FS-SAF-001",
    ):
        assert line in text
    assert text.index("Site Safety Induction") < text.index("Welcome")
    title = chars_of(document, "Site Safety Induction")[0]
    assert title["size"] > chars_of(document, "Welcome")[0]["size"]


def test_front_matter_sets_the_pdf_title_and_footer_reference() -> None:
    document = open_pdf(render(FRONT_MATTER, make_brand()))

    assert document.metadata["Title"] == "Site Safety Induction"
    assert "FS-SAF-001 · Page 1 of 1" in document.pages[0].extract_text()


def test_front_matter_can_override_the_brand() -> None:
    markdown = '---\nbrand:\n  colors:\n    primary: "#7A1F3D"\n---\n# Heading\n'

    heading = chars_of(open_pdf(render(markdown, make_brand())), "Heading")[0]

    assert_colour(heading["non_stroking_color"], "#7A1F3D")


def test_bad_brand_override_is_reported() -> None:
    markdown = '---\nbrand:\n  colors:\n    primary: "red"\n---\n# Heading\n'

    with pytest.raises(BrandError) as excinfo:
        render(markdown, make_brand())

    assert "colors.primary: 'red' is not a hex colour" in str(excinfo.value)
    assert "front matter" in str(excinfo.value)


def test_bad_front_matter_raises_a_document_error() -> None:
    with pytest.raises(DocumentError, match="unknown key 'titel'"):
        render("---\ntitel: Oops\n---\nBody", make_brand())


# Visual snapshot (milestone 5 check)


def test_snapshot_rich_blocks(tmp_path: Path) -> None:
    write_logo(tmp_path / "logo.png")
    markdown = (
        FRONT_MATTER
        + "\n"
        + CHECKLIST.replace("# ", "## ")
        + "\n"
        + CALLOUTS
        + "\n"
        + LONG_TABLE.replace("# Stock Take", "## Stock take")
    )

    pdf = render(markdown, make_brand(tmp_path, logo="logo.png"), base_dir=tmp_path)

    assert_matches_snapshot(pdf, "rich-blocks")


def test_long_callout_continues_onto_the_next_page() -> None:
    body = "\n>\n".join(f"> Point {n}: keep to the marked walkways." for n in range(1, 81))

    document = open_pdf(render(f"> [!WARNING]\n{body}\n", make_brand()))

    assert len(document.pages) >= 2
    assert "Point 80: keep to the marked walkways." in document.pages[-1].extract_text()
