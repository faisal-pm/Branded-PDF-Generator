"""Public rendering API (F13)."""

from __future__ import annotations

import io
from functools import partial
from typing import Any

from reportlab.platypus import BaseDocTemplate, Frame, PageTemplate, Spacer

from brandpdf.brand import Brand
from brandpdf.flowables import build_styles, to_flowables
from brandpdf.letterhead import DocumentInfo, Letterhead, NumberedCanvas
from brandpdf.parse import Block, Heading, parse, plain_text


def render(markdown: str, brand: Brand) -> bytes:
    """Render Markdown with a brand kit and return the PDF as bytes.

    The output is deterministic: the same Markdown and brand kit give byte-identical PDFs.
    """
    blocks = parse(markdown)
    story = to_flowables(blocks, build_styles(brand)) or [Spacer(0, 0)]
    letterhead = Letterhead(brand, DocumentInfo(title=_title(blocks) or brand.name))

    def frame(first_page: bool) -> Frame:
        area = letterhead.content_area(first_page)
        # Zero padding, so the content area is exactly where text starts.
        return Frame(
            area.x,
            area.y,
            area.width,
            area.height,
            leftPadding=0,
            rightPadding=0,
            topPadding=0,
            bottomPadding=0,
        )

    def draw_page(canvas: Any, _document: Any) -> None:
        letterhead.draw_page(canvas, canvas.getPageNumber())

    buffer = io.BytesIO()
    document = BaseDocTemplate(
        buffer,
        pagesize=brand.page.dimensions,
        pageTemplates=[
            PageTemplate("first", [frame(True)], onPage=draw_page, autoNextPageTemplate="later"),
            PageTemplate("later", [frame(False)], onPage=draw_page),
        ],
        title=letterhead.info.title,
        author=brand.name,
        creator="brandpdf",
        invariant=True,  # fixed timestamps and document ID
    )
    document.build(story, canvasmaker=partial(NumberedCanvas, footer=letterhead.draw_footer))
    return letterhead.merge_pdf_backgrounds(buffer.getvalue())


def _title(blocks: list[Block]) -> str | None:
    for block in blocks:
        if isinstance(block, Heading) and block.level == 1:
            return plain_text(block.content).strip()
    return None
