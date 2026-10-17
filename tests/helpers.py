"""Shared test helpers: brands, PDF inspection, fixture files and visual snapshots."""

from __future__ import annotations

import io
import os
from pathlib import Path
from typing import Any

import pdfplumber
import pymupdf
import pytest
import reportlab
from PIL import Image, ImageChops
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen.canvas import Canvas

from brandpdf.brand import Brand, parse_brand

VERA = Path(reportlab.__file__).parent / "fonts"
SNAPSHOTS = Path(__file__).parent / "snapshots"
SNAPSHOT_OUTPUT = Path(__file__).parent / "output"
UPDATE_SNAPSHOTS = os.environ.get("BRANDPDF_UPDATE_SNAPSHOTS") == "1"


def make_brand(base_dir: Path | str = ".", **overrides: Any) -> Brand:
    """A fictional brand using the Vera fonts that ship with ReportLab."""
    data: dict[str, Any] = {
        "name": "Fernleaf Studio",
        "colors": {
            "primary": "#2E5E4E",
            "secondary": "#8FB9A8",
            "accent": "#F4A259",
            "text": "#222222",
        },
        "fonts": {"heading": str(VERA / "VeraBd.ttf"), "body": str(VERA / "Vera.ttf")},
        "contact": {
            "address": "12 Willow Lane\nBrookfield",
            "phone": "+00 1234 5678",
            "email": "hello@fernleaf.example",
            "website": "fernleaf.example",
        },
    }
    data.update(overrides)
    return parse_brand(data, base_dir=base_dir)


def open_pdf(pdf: bytes) -> pdfplumber.PDF:
    return pdfplumber.open(io.BytesIO(pdf))


def full_text(document: pdfplumber.PDF) -> str:
    return "\n".join(page.extract_text() for page in document.pages)


def find_chars(page: pdfplumber.page.Page, phrase: str) -> list[dict[str, Any]] | None:
    chars = [c for c in page.chars if c["text"].strip()]
    letters = "".join(c["text"] for c in chars)
    target = phrase.replace(" ", "")
    start = letters.find(target)
    return chars[start : start + len(target)] if start != -1 else None


def chars_of(document: pdfplumber.PDF, phrase: str) -> list[dict[str, Any]]:
    """The characters that spell the first occurrence of ``phrase`` on any page."""
    for page in document.pages:
        found = find_chars(page, phrase)
        if found:
            return found
    raise AssertionError(f"{phrase!r} not found in the PDF")


def rgb(hex_colour: str) -> tuple[float, ...]:
    return tuple(int(hex_colour[i : i + 2], 16) / 255 for i in (1, 3, 5))


def assert_colour(colour: Any, hex_colour: str) -> None:
    assert tuple(colour) == pytest.approx(rgb(hex_colour), abs=0.01)


def mm(value: float) -> float:
    return value * 72 / 25.4


def write_letterhead_pdf(path: Path, label: str, pagesize: tuple[float, float] = A4) -> Path:
    """A fictional one-page letterhead PDF with a coloured band and a text label."""
    canvas = Canvas(str(path), pagesize=pagesize, invariant=True)
    width, height = pagesize
    canvas.setFillColorRGB(0.18, 0.37, 0.31)
    canvas.rect(0, height - 50, width, 50, stroke=0, fill=1)
    canvas.setFillColorRGB(1, 1, 1)
    canvas.setFont("Helvetica-Bold", 14)
    canvas.drawString(40, height - 32, label)
    canvas.setFont("Helvetica", 8)
    canvas.setFillColorRGB(0.3, 0.3, 0.3)
    canvas.drawString(40, 20, f"{label} footer")
    canvas.showPage()
    canvas.save()
    return path


def write_letterhead_png(path: Path, band: str = "#2E5E4E") -> Path:
    """A fictional A4-proportioned letterhead image with a coloured top band."""
    image = Image.new("RGB", (595, 842), "white")
    image.paste(Image.new("RGB", (595, 60), band), (0, 0))
    image.save(path)
    return path


def write_logo(path: Path, colour: str = "#2E5E4E") -> Path:
    image = Image.new("RGB", (240, 80), "white")
    image.paste(Image.new("RGB", (80, 80), colour), (0, 0))
    image.save(path)
    return path


def page_images(pdf: bytes, dpi: int = 50) -> list[Image.Image]:
    with pymupdf.open(stream=pdf, filetype="pdf") as document:
        return [
            Image.frombytes("RGB", (pix.width, pix.height), pix.samples)
            for pix in (page.get_pixmap(dpi=dpi, alpha=False) for page in document)
        ]


def assert_matches_snapshot(pdf: bytes, name: str, tolerance: float = 0.002) -> None:
    """Compare every page against ``tests/snapshots/<name>-p<n>.png``.

    A pixel counts as different when any channel is off by more than 32 levels; the page passes
    when no more than ``tolerance`` of its pixels differ. Run with BRANDPDF_UPDATE_SNAPSHOTS=1 to
    accept the current output as the new reference.
    """
    pages = page_images(pdf)
    if UPDATE_SNAPSHOTS:
        SNAPSHOTS.mkdir(exist_ok=True)
        for stale in SNAPSHOTS.glob(f"{name}-p*.png"):
            stale.unlink()
        for number, image in enumerate(pages, 1):
            image.save(SNAPSHOTS / f"{name}-p{number}.png", optimize=True)
        return

    references = sorted(SNAPSHOTS.glob(f"{name}-p*.png"))
    assert references, (
        f"No snapshot for {name!r}. Run BRANDPDF_UPDATE_SNAPSHOTS=1 pytest to create it."
    )
    assert len(pages) == len(references), f"{name}: {len(pages)} pages, expected {len(references)}"

    for number, actual in enumerate(pages, 1):
        expected = Image.open(SNAPSHOTS / f"{name}-p{number}.png").convert("RGB")
        assert actual.size == expected.size, f"{name} page {number}: size changed"
        difference = (
            ImageChops.difference(actual, expected)
            .convert("L")
            .point(lambda level: 255 if level > 32 else 0)
        )
        changed = sum(difference.histogram()[255:]) / (actual.width * actual.height)
        if changed > tolerance:
            SNAPSHOT_OUTPUT.mkdir(exist_ok=True)
            actual.save(SNAPSHOT_OUTPUT / f"{name}-p{number}.png")
            raise AssertionError(
                f"{name} page {number}: {changed:.2%} of pixels differ "
                f"(see tests/output/{name}-p{number}.png)"
            )
