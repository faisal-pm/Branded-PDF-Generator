"""Draw the logos and letterheads for the fictional example brands.

Every brand, name and address here is invented. Run from the repo root:

    uv run python scripts/make_example_assets.py
"""

from __future__ import annotations

import math
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont
from reportlab.lib.colors import HexColor
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen.canvas import Canvas

EXAMPLES = Path(__file__).resolve().parent.parent / "examples"
FONTS = EXAMPLES / "fonts"
SCALE = 4  # draw logos at 4x and keep them sharp when scaled down in the PDF


def font(path: str, size: int) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(str(FONTS / path), size * SCALE)


def fernleaf_logo(target: Path) -> None:
    """A leaf mark beside a serif wordmark."""
    green, sage = "#2E5E4E", "#8FB9A8"
    image = Image.new("RGBA", (300 * SCALE, 80 * SCALE), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    s = SCALE
    draw.ellipse((6 * s, 14 * s, 46 * s, 74 * s), fill=sage)
    draw.ellipse((22 * s, 6 * s, 62 * s, 66 * s), fill=green)
    draw.line((34 * s, 66 * s, 34 * s, 22 * s), fill="white", width=2 * s)
    draw.text(
        (74 * s, 10 * s),
        "Fernleaf",
        font=font("dm-serif-display/DMSerifDisplay-Regular.ttf", 34),
        fill=green,
    )
    draw.text(
        (76 * s, 52 * s), "LANDSCAPE STUDIO", font=font("lato/Lato-Regular.ttf", 12), fill="#5B6B63"
    )
    image.save(target, optimize=True)


def kestrel_logo(target: Path, light: bool = False) -> None:
    """A wing-shaped chevron beside a geometric wordmark (light version for dark bands)."""
    ink, orange = ("white" if light else "#1B2A41"), "#F25F3A"
    image = Image.new("RGBA", (280 * SCALE, 64 * SCALE), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    s = SCALE
    draw.polygon(
        [(4 * s, 52 * s), (30 * s, 8 * s), (40 * s, 26 * s), (22 * s, 52 * s)], fill=orange
    )
    draw.polygon([(26 * s, 52 * s), (44 * s, 26 * s), (58 * s, 52 * s)], fill=ink)
    draw.text(
        (70 * s, 10 * s), "KESTREL LABS", font=font("poppins/Poppins-SemiBold.ttf", 28), fill=ink
    )
    image.save(target, optimize=True)


def kestrel_letterheads(first: Path, later: Path, logo: Path) -> None:
    """First-page and continuation letterhead PDFs, as a print designer might supply them."""
    pdfmetrics.registerFont(TTFont("Poppins", str(FONTS / "poppins/Poppins-Regular.ttf")))
    navy, orange = HexColor("#1B2A41"), HexColor("#F25F3A")
    width, height = A4

    for path, details in ((first, True), (later, False)):
        canvas = Canvas(str(path), pagesize=A4, invariant=True)
        canvas.setFillColor(navy)
        canvas.rect(0, height - 30 * mm, width, 30 * mm, stroke=0, fill=1)
        canvas.setFillColor(orange)
        canvas.rect(0, height - 31.5 * mm, width, 1.5 * mm, stroke=0, fill=1)
        canvas.drawImage(
            str(logo), 18 * mm, height - 21 * mm, 62 * mm, 62 * mm * 64 / 280, mask="auto"
        )
        if details:
            canvas.setFillColor(HexColor("#FFFFFF"))
            canvas.setFont("Poppins", 7.5)
            lines = ["Unit 4, Harrow Works", "Eastmere Industrial Park", "labs@kestrel.example"]
            for n, line in enumerate(lines):
                canvas.drawRightString(width - 18 * mm, height - (11 + n * 4) * mm, line)
            canvas.setFillColor(navy)
            canvas.rect(0, 0, width, 6 * mm, stroke=0, fill=1)
        canvas.showPage()
        canvas.save()


def tidewell_logo(target: Path) -> None:
    """Three waves in a circle beside a humanist wordmark."""
    teal, foam = "#0F6E7A", "#A7D7D9"
    image = Image.new("RGBA", (340 * SCALE, 80 * SCALE), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    s = SCALE
    draw.ellipse((4 * s, 6 * s, 72 * s, 74 * s), fill=teal)
    for row, colour in enumerate(("white", foam, "white")):
        y = (28 + row * 12) * s
        points = [(x * s, y + math.sin(x / 6) * 3 * s) for x in range(14, 63)]
        draw.line(points, fill=colour, width=3 * s)
    draw.text(
        (86 * s, 10 * s), "Tidewell", font=font("pt-sans/PT_Sans-Web-Bold.ttf", 30), fill=teal
    )
    draw.text(
        (88 * s, 48 * s),
        "Community Health",
        font=font("pt-sans/PT_Sans-Web-Regular.ttf", 17),
        fill="#3C5A5E",
    )
    image.save(target, optimize=True)


def tidewell_letterhead(target: Path, logo: Path) -> None:
    """A US Letter background image at 150 dpi: logo top left, a wave along the foot."""
    width, height = 1275, 1650
    image = Image.new("RGB", (width, height), "white")
    mark = Image.open(logo)
    mark = mark.resize((420, round(420 * mark.height / mark.width)), Image.LANCZOS)
    image.paste(mark, (112, 70), mark)
    draw = ImageDraw.Draw(image)
    draw.text(
        (width - 112, 92),
        "41 Harbour Road, Saltmarsh",
        font=ImageFont.truetype(str(FONTS / "pt-sans/PT_Sans-Web-Regular.ttf"), 22),
        fill="#3C5A5E",
        anchor="ra",
    )
    draw.text(
        (width - 112, 124),
        "clinic@tidewell.example",
        font=ImageFont.truetype(str(FONTS / "pt-sans/PT_Sans-Web-Regular.ttf"), 22),
        fill="#3C5A5E",
        anchor="ra",
    )
    for offset, colour in ((0, "#A7D7D9"), (18, "#0F6E7A")):
        top = height - 90 + offset
        wave = [(x, top + math.sin(x / 70) * 12) for x in range(0, width + 1, 4)]
        draw.polygon([*wave, (width, height), (0, height)], fill=colour)
    image.save(target, optimize=True)


def main() -> None:
    fernleaf_logo(EXAMPLES / "fernleaf-studio" / "logo.png")
    kestrel = EXAMPLES / "kestrel-labs"
    kestrel_logo(kestrel / "logo-light.png", light=True)
    kestrel_letterheads(
        kestrel / "letterhead-first.pdf",
        kestrel / "letterhead-continuation.pdf",
        kestrel / "logo-light.png",
    )
    tidewell = EXAMPLES / "tidewell-health"
    tidewell_logo(tidewell / "logo.png")
    tidewell_letterhead(tidewell / "letterhead.png", tidewell / "logo.png")


if __name__ == "__main__":
    main()
