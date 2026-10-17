"""Background and generated letterheads, page numbers (F3-F5, F10)."""

from __future__ import annotations

from reportlab.lib.colors import HexColor
from reportlab.pdfgen.canvas import Canvas

from brandpdf.brand import Brand


def paint_background(canvas: Canvas, brand: Brand) -> None:
    """Fill the page with the brand background colour, unless it is plain white."""
    if brand.colors.background == "#FFFFFF":
        return
    width, height = brand.page.dimensions
    canvas.saveState()
    canvas.setFillColor(HexColor(brand.colors.background))
    canvas.rect(0, 0, width, height, stroke=0, fill=1)
    canvas.restoreState()
