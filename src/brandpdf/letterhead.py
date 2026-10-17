"""Background and generated letterheads, page numbers (F3-F5, F10).

Two modes, chosen by whether the brand kit names a letterhead file:

- Background: a PDF, PNG or JPEG fills each page, with a separate file for continuation pages
  if one is given. Images are drawn by ReportLab under the content; PDF pages are merged under
  each finished page with pypdf, since ReportLab cannot import PDF pages itself.
- Generated: a header (colour band, logo or name, contact block) and a footer contact line are
  drawn from the brand kit. Continuation pages get a compact header with the document title.

Both modes number pages "Page 2 of 5", which needs the page count, so the footer is drawn by
``NumberedCanvas`` once every page has been laid out.
"""

from __future__ import annotations

import io
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from pypdf import PdfReader, PdfWriter, Transformation
from reportlab.lib.colors import HexColor
from reportlab.lib.units import mm
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen.canvas import Canvas

from brandpdf.brand import IMAGE_SUFFIXES, Brand
from brandpdf.flowables import register_font

# Generated letterhead layout, measured from the page edges.
BAND_HEIGHT = 4 * mm
FIRST_HEADER_SPACE = 38 * mm  # body text starts at least this far from the top of page 1
LATER_HEADER_SPACE = 21 * mm  # ... and of continuation pages
FOOTER_SPACE = 20 * mm  # body text ends at least this far from the bottom
LOGO_TOP = 10 * mm
LOGO_MAX_HEIGHT = 16 * mm
LOGO_MAX_WIDTH = 60 * mm
FIRST_RULE = 32 * mm
LATER_TEXT = 12 * mm
LATER_RULE = 15 * mm
FOOTER_RULE = 15 * mm
FOOTER_TEXT = 10 * mm

NAME_SIZE = 16.0
CONTACT_SIZE = 8.0
SMALL_SIZE = 7.5


@dataclass(frozen=True)
class DocumentInfo:
    """Per-document details shown in headers and footers."""

    title: str
    reference: str | None = None


@dataclass(frozen=True)
class Area:
    """A rectangle in PDF points, origin at the bottom-left of the page."""

    x: float
    y: float
    width: float
    height: float


class Letterhead:
    def __init__(self, brand: Brand, info: DocumentInfo) -> None:
        self.brand = brand
        self.info = info
        self.width, self.height = brand.page.dimensions
        self.heading_font = register_font(brand.fonts.heading)
        self.body_font = register_font(brand.fonts.body)

    @property
    def generated(self) -> bool:
        return self.brand.letterhead.first_page is None

    def background_for(self, page_number: int) -> Path | None:
        letterhead = self.brand.letterhead
        if page_number == 1 or letterhead.continuation is None:
            return letterhead.first_page
        return letterhead.continuation

    def content_area(self, first_page: bool) -> Area:
        """Where body text may flow. Generated headers and footers claim space of their own."""
        margins = self.brand.page.margins_mm
        top, bottom = margins.top * mm, margins.bottom * mm
        if self.generated:
            top = max(top, FIRST_HEADER_SPACE if first_page else LATER_HEADER_SPACE)
            bottom = max(bottom, FOOTER_SPACE)
        left, right = margins.left * mm, margins.right * mm
        return Area(left, bottom, self.width - left - right, self.height - top - bottom)

    def draw_page(self, canvas: Canvas, page_number: int) -> None:
        """Draw everything that sits under the body text. Called as each page starts."""
        background = self.background_for(page_number)
        if background is None:
            self._paint_background_colour(canvas)
        elif background.suffix.lower() in IMAGE_SUFFIXES:
            canvas.drawImage(str(background), 0, 0, self.width, self.height, mask="auto")
        if self.generated:
            canvas.saveState()
            canvas.setFillColor(HexColor(self.brand.colors.primary))
            canvas.rect(0, self.height - BAND_HEIGHT, self.width, BAND_HEIGHT, stroke=0, fill=1)
            if page_number == 1:
                self._first_page_header(canvas)
            else:
                self._continuation_header(canvas)
            canvas.restoreState()

    def draw_footer(self, canvas: Canvas, page_number: int, page_count: int) -> None:
        """Draw the footer once the page count is known."""
        margins = self.brand.page.margins_mm
        left, right = margins.left * mm, self.width - margins.right * mm
        numbering = f"Page {page_number} of {page_count}"
        if self.info.reference:
            numbering = f"{self.info.reference} · {numbering}"

        canvas.saveState()
        canvas.setFont(self.body_font, SMALL_SIZE)
        canvas.setFillColor(HexColor(self.brand.colors.text))
        if self.generated:
            canvas.setStrokeColor(HexColor(self.brand.colors.secondary))
            canvas.setLineWidth(0.5)
            canvas.line(left, FOOTER_RULE, right, FOOTER_RULE)
            if line := self._contact_line():
                canvas.drawString(left, FOOTER_TEXT, line)
            canvas.drawRightString(right, FOOTER_TEXT, numbering)
        else:
            # The supplied letterhead owns the margins; keep the number small and low.
            canvas.drawRightString(right, max(margins.bottom * mm / 2, 6 * mm), numbering)
        canvas.restoreState()

    def merge_pdf_backgrounds(self, pdf: bytes) -> bytes:
        """Place PDF letterhead pages under the rendered pages, scaled to fit."""
        letterhead = self.brand.letterhead
        files = {
            path
            for path in (letterhead.first_page, letterhead.continuation)
            if path is not None and path.suffix.lower() == ".pdf"
        }
        if not files:
            return pdf

        backgrounds = {path: PdfReader(path).pages[0] for path in files}
        writer = PdfWriter(clone_from=io.BytesIO(pdf))  # keeps the metadata
        for number, page in enumerate(writer.pages, 1):
            background = backgrounds.get(self.background_for(number))  # type: ignore[arg-type]
            if background is not None:
                box = background.mediabox
                fit = (
                    Transformation()
                    .translate(-float(box.left), -float(box.bottom))
                    .scale(
                        float(page.mediabox.width) / float(box.width),
                        float(page.mediabox.height) / float(box.height),
                    )
                )
                page.merge_transformed_page(background, fit, over=False)
        output = io.BytesIO()
        writer.write(output)
        return output.getvalue()

    def _paint_background_colour(self, canvas: Canvas) -> None:
        if self.brand.colors.background == "#FFFFFF":
            return
        canvas.saveState()
        canvas.setFillColor(HexColor(self.brand.colors.background))
        canvas.rect(0, 0, self.width, self.height, stroke=0, fill=1)
        canvas.restoreState()

    def _first_page_header(self, canvas: Canvas) -> None:
        margins = self.brand.page.margins_mm
        left, right = margins.left * mm, self.width - margins.right * mm
        colors = self.brand.colors

        if self.brand.logo is not None:
            logo = ImageReader(str(self.brand.logo))
            image_width, image_height = logo.getSize()
            scale = min(LOGO_MAX_HEIGHT / image_height, LOGO_MAX_WIDTH / image_width)
            width, height = image_width * scale, image_height * scale
            canvas.drawImage(
                logo, left, self.height - LOGO_TOP - height, width, height, mask="auto"
            )
        else:
            canvas.setFont(self.heading_font, NAME_SIZE)
            canvas.setFillColor(HexColor(colors.primary))
            canvas.drawString(left, self.height - LOGO_TOP - NAME_SIZE, self.brand.name)

        canvas.setFont(self.body_font, CONTACT_SIZE)
        canvas.setFillColor(HexColor(colors.text))
        y = self.height - LOGO_TOP - CONTACT_SIZE
        for line in self._contact_block():
            canvas.drawRightString(right, y, line)
            y -= CONTACT_SIZE * 1.35

        canvas.setStrokeColor(HexColor(colors.secondary))
        canvas.setLineWidth(0.75)
        canvas.line(left, self.height - FIRST_RULE, right, self.height - FIRST_RULE)

    def _continuation_header(self, canvas: Canvas) -> None:
        margins = self.brand.page.margins_mm
        left, right = margins.left * mm, self.width - margins.right * mm
        colors = self.brand.colors

        canvas.setFont(self.heading_font, CONTACT_SIZE + 1)
        canvas.setFillColor(HexColor(colors.primary))
        canvas.drawString(left, self.height - LATER_TEXT, self.brand.name)
        if self.info.title != self.brand.name:
            canvas.setFont(self.body_font, CONTACT_SIZE + 1)
            canvas.setFillColor(HexColor(colors.text))
            canvas.drawRightString(right, self.height - LATER_TEXT, self.info.title)

        canvas.setStrokeColor(HexColor(colors.secondary))
        canvas.setLineWidth(0.5)
        canvas.line(left, self.height - LATER_RULE, right, self.height - LATER_RULE)

    def _contact_block(self) -> list[str]:
        contact = self.brand.contact
        lines = (contact.address or "").splitlines()
        lines += [contact.phone or "", contact.email or "", contact.website or ""]
        return [line.strip() for line in lines if line.strip()]

    def _contact_line(self) -> str:
        contact = self.brand.contact
        parts = (contact.website, contact.email, contact.phone)
        return " · ".join(part.strip() for part in parts if part and part.strip())


class NumberedCanvas(Canvas):
    """A canvas that holds every page until the end, so footers can say "Page 2 of 5"."""

    def __init__(
        self, *args: Any, footer: Callable[[Canvas, int, int], None], **kwargs: Any
    ) -> None:
        super().__init__(*args, **kwargs)
        self._footer = footer
        self._saved_pages: list[dict[str, Any]] = []

    def showPage(self) -> None:  # noqa: N802 - ReportLab's name
        self._saved_pages.append(dict(self.__dict__))
        self._startPage()

    def save(self) -> None:
        page_count = len(self._saved_pages)
        for number, state in enumerate(self._saved_pages, 1):
            self.__dict__.update(state)
            self._footer(self, number, page_count)
            super().showPage()
        super().save()
