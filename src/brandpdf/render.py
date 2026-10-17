"""Public rendering API (F13)."""

from __future__ import annotations

import io
from functools import partial
from pathlib import Path
from typing import Any

from reportlab.platypus import BaseDocTemplate, Frame, PageTemplate, Spacer

from brandpdf.brand import Brand, override_brand
from brandpdf.flowables import build_styles, title_block, to_flowables
from brandpdf.letterhead import DocumentInfo, Letterhead, NumberedCanvas
from brandpdf.parse import Block, Heading, parse_document, plain_text


def render(markdown: str, brand: Brand, *, base_dir: str | Path | None = None) -> bytes:
    """Render Markdown with a brand kit and return the PDF as bytes.

    Front matter at the top of ``markdown`` can set a title block, a footer reference and
    brand overrides. Images and override paths resolve against ``base_dir`` (default: the
    working directory). The same inputs always give byte-identical PDFs.

    Raises ``DocumentError`` for problems in the document and ``BrandError`` for bad overrides.
    """
    folder = Path(base_dir) if base_dir is not None else Path.cwd()
    document = parse_document(markdown)
    meta, blocks = document.meta, document.blocks
    brand = override_brand(brand, meta.brand, base_dir=folder)

    info = DocumentInfo(title=meta.title or _title(blocks) or brand.name, reference=meta.reference)
    letterhead = Letterhead(brand, info)
    styles = build_styles(brand)
    page_height = min(letterhead.content_area(True).height, letterhead.content_area(False).height)
    story = title_block(meta, styles) + to_flowables(
        blocks, styles, base_dir=folder, max_image_height=page_height
    )
    story = story or [Spacer(0, 0)]

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
    template = BaseDocTemplate(
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
    template.build(story, canvasmaker=partial(NumberedCanvas, footer=letterhead.draw_footer))
    return letterhead.merge_pdf_backgrounds(buffer.getvalue())


def _title(blocks: list[Block]) -> str | None:
    for block in blocks:
        if isinstance(block, Heading) and block.level == 1:
            return plain_text(block.content).strip()
    return None
