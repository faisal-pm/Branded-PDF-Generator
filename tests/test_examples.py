"""Shipped examples render, match their snapshots, and their committed PDFs are current (F15)."""

from pathlib import Path

import pytest
from helpers import assert_matches_snapshot, open_pdf

from brandpdf import load_brand, render

EXAMPLES = Path(__file__).resolve().parent.parent / "examples"
DOCUMENTS = sorted(EXAMPLES.glob("*/*.md"))


def test_there_are_examples_for_every_letterhead_mode() -> None:
    modes = set()
    for kit in EXAMPLES.glob("*/brand.yaml"):
        letterhead = load_brand(kit).letterhead.first_page
        modes.add("generated" if letterhead is None else letterhead.suffix)

    assert modes == {"generated", ".pdf", ".png"}


@pytest.mark.parametrize("source", DOCUMENTS, ids=lambda path: f"{path.parent.name}/{path.stem}")
def test_example_matches_its_snapshot(source: Path) -> None:
    pdf = render(
        source.read_text(encoding="utf-8"),
        load_brand(source.parent / "brand.yaml"),
        base_dir=source.parent,
    )

    assert_matches_snapshot(pdf, f"example-{source.parent.name}-{source.stem}")


@pytest.mark.parametrize("source", DOCUMENTS, ids=lambda path: f"{path.parent.name}/{path.stem}")
def test_committed_example_pdf_is_up_to_date(source: Path) -> None:
    """Run scripts/build_examples.py if this fails."""
    committed = source.with_suffix(".pdf")
    fresh = render(
        source.read_text(encoding="utf-8"),
        load_brand(source.parent / "brand.yaml"),
        base_dir=source.parent,
    )

    assert committed.is_file(), f"{committed.name} is missing"
    old, new = open_pdf(committed.read_bytes()), open_pdf(fresh)
    assert [page.extract_text() for page in old.pages] == [
        page.extract_text() for page in new.pages
    ]
