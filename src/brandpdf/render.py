"""Public rendering API (F13)."""

from __future__ import annotations

import io
from typing import Any

from reportlab.lib.units import mm
from reportlab.platypus import BaseDocTemplate, Frame, PageTemplate, Spacer

from brandpdf.brand import Brand
from brandpdf.flowables import build_styles, to_flowables
from brandpdf.letterhead import paint_background
from brandpdf.parse import Block, Heading, parse, plain_text


def render(markdown: str, brand: Brand) -> bytes:
    """Render Markdown with a brand kit and return the PDF as bytes.

    The output is deterministic: the same Markdown and brand kit give byte-identical PDFs.
    """
    blocks = parse(markdown)
    story = to_flowables(blocks, build_styles(brand)) or [Spacer(0, 0)]
    width, height = brand.page.dimensions
    margins = brand.page.margins_mm
    # Zero padding, so the brand margins are exactly where text starts.
    body = Frame(
        margins.left * mm,
        margins.bottom * mm,
        width - (margins.left + margins.right) * mm,
        height - (margins.top + margins.bottom) * mm,
        leftPadding=0,
        rightPadding=0,
        topPadding=0,
        bottomPadding=0,
        id="body",
    )

    def draw_page(canvas: Any, _document: Any) -> None:
        paint_background(canvas, brand)

    buffer = io.BytesIO()
    document = BaseDocTemplate(
        buffer,
        pagesize=(width, height),
        pageTemplates=[PageTemplate(id="page", frames=[body], onPage=draw_page)],
        title=_title(blocks) or brand.name,
        author=brand.name,
        creator="brandpdf",
        invariant=True,  # fixed timestamps and document ID
    )
    document.build(story)
    return buffer.getvalue()


def _title(blocks: list[Block]) -> str | None:
    for block in blocks:
        if isinstance(block, Heading) and block.level == 1:
            return plain_text(block.content).strip()
    return None
