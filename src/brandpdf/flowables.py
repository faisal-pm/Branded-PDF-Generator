"""Blocks to Platypus flowables, including checklist and callout styles (F6-F9, F11).

Every visual decision (sizes, spacing, which brand colour goes where) lives in ``build_styles``,
so the mapping from blocks to flowables stays a plain translation.
"""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from pathlib import Path
from xml.sax.saxutils import escape

from reportlab.lib.colors import Color, HexColor, white
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    CondPageBreak,
    Flowable,
    HRFlowable,
    ListFlowable,
    Preformatted,
    Spacer,
    TableStyle,
)
from reportlab.platypus import ListItem as PdfListItem
from reportlab.platypus import Paragraph as PdfParagraph
from reportlab.platypus import Table as PdfTable

from brandpdf.brand import IMAGE_SUFFIXES, Brand
from brandpdf.errors import DocumentError
from brandpdf.parse import (
    Block,
    Callout,
    CodeBlock,
    FrontMatter,
    Heading,
    Image,
    Inline,
    LineBreak,
    ListBlock,
    Paragraph,
    Quote,
    Rule,
    Table,
    plain_text,
)

BODY_SIZE = 10.5
TITLE_SIZE = 26.0
HEADING_SIZES = {1: 22.0, 2: 16.0, 3: 13.0}  # deeper headings use the level 3 style
CODE_FONT = "Courier"
BULLETS = ("•", "–")  # alternate by nesting depth
LIST_INDENT = 16.0
CHECKBOX_SIZE = 9.0
KEEP_WITH_HEADING = 3 * BODY_SIZE * 1.4  # room for three body lines under a heading
CELL_PADDING = 5.0
PIXELS_PER_POINT = 96 / 72  # images without size hints are treated as 96 dpi, like browsers
ALIGNMENTS = {None: TA_LEFT, "left": TA_LEFT, "center": TA_CENTER, "right": TA_RIGHT}
_REMOTE = re.compile(r"^[a-z][a-z0-9+.-]*://", re.IGNORECASE)


@dataclass(frozen=True)
class Styles:
    body: ParagraphStyle
    list_item: ParagraphStyle
    headings: dict[int, ParagraphStyle]
    code: ParagraphStyle
    title: ParagraphStyle
    subtitle: ParagraphStyle
    details: ParagraphStyle
    table_header: ParagraphStyle
    table_cell: ParagraphStyle
    callout_label: ParagraphStyle
    primary: Color
    secondary: Color
    accent: Color
    background: Color
    zebra: Color
    link: str


def register_font(font: str | Path) -> str:
    """Return a ReportLab font name for a brand font, registering TrueType files once."""
    if isinstance(font, str):
        return font
    digest = hashlib.sha256(str(font).encode()).hexdigest()[:8]
    name = f"{font.stem}-{digest}"
    if name not in pdfmetrics.getRegisteredFontNames():
        pdfmetrics.registerFont(TTFont(name, str(font)))
        # A single file has no bold or italic face, so <b> and <i> fall back to the same face.
        pdfmetrics.registerFontFamily(name, normal=name, bold=name, italic=name, boldItalic=name)
    return name


def tint(colour: Color, strength: float, base: Color = white) -> Color:
    """``colour`` mixed into ``base``; strength 0 gives the base, 1 the colour itself."""
    pairs = zip(colour.rgb(), base.rgb(), strict=True)
    return Color(*(below + (above - below) * strength for above, below in pairs))


def luminance(colour: Color) -> float:
    red, green, blue = colour.rgb()
    return 0.2126 * red + 0.7152 * green + 0.0722 * blue


def readable_on(background: str, dark_text: str) -> Color:
    """White text on dark fills, the brand's text colour on light ones."""
    return white if luminance(HexColor(background)) < 0.6 else HexColor(dark_text)


def legible(colour: Color, text: Color) -> Color:
    """``colour`` for text on a light page, pulled towards the text colour if it is too pale."""
    return colour if luminance(colour) < 0.45 else tint(colour, 0.45, text)


def build_styles(brand: Brand) -> Styles:
    colors = brand.colors
    body_font = register_font(brand.fonts.body)
    heading_font = register_font(brand.fonts.heading)
    body = ParagraphStyle(
        "brand-body",
        fontName=body_font,
        fontSize=BODY_SIZE,
        leading=BODY_SIZE * 1.4,
        textColor=HexColor(colors.text),
        spaceAfter=BODY_SIZE * 0.6,
    )
    headings = {
        level: ParagraphStyle(
            f"brand-h{level}",
            parent=body,
            fontName=heading_font,
            fontSize=size,
            leading=size * 1.25,
            textColor=HexColor(colors.primary),
            spaceBefore=size * 0.6,
            spaceAfter=size * 0.4,
        )
        for level, size in HEADING_SIZES.items()
    }
    small = BODY_SIZE * 0.9
    return Styles(
        body=body,
        list_item=ParagraphStyle("brand-list-item", parent=body, spaceAfter=BODY_SIZE * 0.25),
        headings=headings,
        code=ParagraphStyle(
            "brand-code",
            parent=body,
            fontName=CODE_FONT,
            fontSize=BODY_SIZE * 0.85,
            leading=BODY_SIZE * 1.2,
            leftIndent=LIST_INDENT / 2,
            spaceBefore=BODY_SIZE * 0.2,
            spaceAfter=BODY_SIZE * 0.8,
        ),
        title=ParagraphStyle(
            "brand-title",
            parent=headings[1],
            fontSize=TITLE_SIZE,
            leading=TITLE_SIZE * 1.2,
            spaceBefore=0,
            spaceAfter=BODY_SIZE * 0.5,
        ),
        subtitle=ParagraphStyle(
            "brand-subtitle",
            parent=body,
            fontSize=BODY_SIZE * 1.3,
            leading=BODY_SIZE * 1.7,
            spaceAfter=BODY_SIZE * 0.3,
        ),
        details=ParagraphStyle(
            "brand-details", parent=body, fontSize=small, leading=small * 1.4, spaceAfter=0
        ),
        table_header=ParagraphStyle(
            "brand-table-header",
            parent=body,
            fontName=heading_font,
            fontSize=small,
            leading=small * 1.3,
            textColor=readable_on(colors.primary, colors.text),
            spaceAfter=0,
        ),
        table_cell=ParagraphStyle(
            "brand-table-cell", parent=body, fontSize=small, leading=small * 1.35, spaceAfter=0
        ),
        callout_label=ParagraphStyle(
            "brand-callout-label",
            parent=body,
            fontName=heading_font,
            spaceAfter=BODY_SIZE * 0.2,
        ),
        primary=HexColor(colors.primary),
        secondary=HexColor(colors.secondary),
        accent=HexColor(colors.accent),
        background=HexColor(colors.background),
        zebra=tint(HexColor(colors.secondary), 0.15, HexColor(colors.background)),
        link=colors.primary,
    )


def to_flowables(
    blocks: list[Block] | tuple[Block, ...],
    styles: Styles,
    base_dir: Path = Path("."),
    max_image_height: float = 600.0,
) -> list[Flowable]:
    """Flowables for ``blocks``. Image paths resolve against ``base_dir``."""
    return _Builder(styles, Path(base_dir), max_image_height).flowables(blocks, 0, nested=False)


def title_block(meta: FrontMatter, styles: Styles) -> list[Flowable]:
    """The title, subtitle and date/reference line from a document's front matter."""
    out: list[Flowable] = []
    if meta.title:
        out.append(PdfParagraph(escape(meta.title), styles.title))
    if meta.subtitle:
        out.append(PdfParagraph(escape(meta.subtitle), styles.subtitle))
    if details := " · ".join(part for part in (meta.date, meta.reference) if part):
        out.append(PdfParagraph(escape(details), styles.details))
    if out:
        out.append(
            HRFlowable(
                width="100%",
                thickness=0.75,
                color=styles.secondary,
                spaceBefore=BODY_SIZE * 0.6,
                spaceAfter=BODY_SIZE * 0.8,
            )
        )
    return out


def markup(content: tuple[Inline, ...], styles: Styles) -> str:
    """ReportLab paragraph markup for inline content; all user text is XML-escaped."""
    parts = []
    for span in content:
        if isinstance(span, LineBreak):
            parts.append("<br/>")
            continue
        text = escape(span.text)
        if span.code:
            text = f'<font face="{CODE_FONT}">{text}</font>'
        if span.italic:
            text = f"<i>{text}</i>"
        if span.bold:
            text = f"<b>{text}</b>"
        if span.href:
            href = escape(span.href, {'"': "&quot;"})
            text = f'<a href="{href}" color="{styles.link}"><u>{text}</u></a>'
        parts.append(text)
    return "".join(parts)


class CheckBox(Flowable):
    """A checklist tick box: an outline when open, filled with a white tick when done."""

    def __init__(self, checked: bool, colour: Color, size: float = CHECKBOX_SIZE) -> None:
        super().__init__()
        self.checked = checked
        self.colour = colour
        self.size = size

    def wrap(self, available_width: float, available_height: float) -> tuple[float, float]:
        return self.size, self.size

    def draw(self) -> None:
        canvas, size = self.canv, self.size
        canvas.setStrokeColor(self.colour)
        canvas.setFillColor(self.colour)
        canvas.setLineWidth(1)
        canvas.rect(0, 0, size, size, stroke=1, fill=1 if self.checked else 0)
        if self.checked:
            canvas.setStrokeColor(white)
            canvas.setLineWidth(1.4)
            tick = canvas.beginPath()
            tick.moveTo(size * 0.22, size * 0.52)
            tick.lineTo(size * 0.42, size * 0.3)
            tick.lineTo(size * 0.78, size * 0.72)
            canvas.drawPath(tick, stroke=1, fill=0)


class FitImage(Flowable):
    """An image shown at its natural size, shrunk to fit the column and page if needed."""

    def __init__(self, path: Path, max_height: float) -> None:
        super().__init__()
        self.image = ImageReader(str(path))
        pixel_width, pixel_height = self.image.getSize()
        self.natural = (pixel_width / PIXELS_PER_POINT, pixel_height / PIXELS_PER_POINT)
        self.max_height = max_height
        self.spaceBefore = BODY_SIZE * 0.3
        self.spaceAfter = BODY_SIZE * 0.8

    def wrap(self, available_width: float, available_height: float) -> tuple[float, float]:
        width, height = self.natural
        scale = min(1.0, available_width / width, self.max_height / height)
        self.width, self.height = width * scale, height * scale
        return self.width, self.height

    def draw(self) -> None:
        self.canv.drawImage(self.image, 0, 0, self.width, self.height, mask="auto")


class _Builder:
    def __init__(self, styles: Styles, base_dir: Path, max_image_height: float) -> None:
        self.styles = styles
        self.base_dir = base_dir
        self.max_image_height = max_image_height

    def flowables(
        self, blocks: list[Block] | tuple[Block, ...], depth: int, nested: bool
    ) -> list[Flowable]:
        styles = self.styles
        out: list[Flowable] = []
        for block in blocks:
            match block:
                case Heading(level=level, content=content):
                    style = styles.headings[min(level, max(HEADING_SIZES))]
                    if out and not nested:
                        # Start a new page rather than strand a heading at the bottom of one.
                        # (keepWithNext would drag a long table along to the next page too.)
                        out.append(CondPageBreak(style.leading + KEEP_WITH_HEADING))
                    out.append(PdfParagraph(markup(content, styles), style))
                case Paragraph(content=content):
                    style = styles.list_item if nested else styles.body
                    out.append(PdfParagraph(markup(content, styles), style))
                case ListBlock() if any(item.checked is not None for item in block.items):
                    out.append(self.checklist(block, depth))
                case ListBlock():
                    out.append(self.bullet_list(block, depth))
                case CodeBlock(text=text):
                    out.append(Preformatted(text, styles.code))
                case Quote(blocks=children):
                    out.append(self.quote(children, depth))
                case Callout():
                    out.append(self.callout(block, depth))
                case Table():
                    out.append(self.table(block))
                case Image():
                    out.append(FitImage(self.image_path(block), self.max_image_height))
                case Rule():
                    out.append(
                        HRFlowable(
                            width="100%",
                            thickness=0.75,
                            color=styles.secondary,
                            spaceBefore=BODY_SIZE * 0.4,
                            spaceAfter=BODY_SIZE,
                        )
                    )
        return out

    def bullet_list(self, block: ListBlock, depth: int) -> ListFlowable:
        items = [
            PdfListItem(self.flowables(item.blocks, depth + 1, nested=True) or [Spacer(0, 0)])
            for item in block.items
        ]
        options = {
            "leftIndent": LIST_INDENT,
            "bulletColor": self.styles.accent,
            "bulletFontName": self.styles.body.fontName,
            "bulletFontSize": self.styles.body.fontSize,
            "spaceAfter": BODY_SIZE * 0.4 if depth == 0 else 0,
        }
        if block.ordered:
            return ListFlowable(
                items, bulletType="1", start=block.start, bulletFormat="%s.", **options
            )
        return ListFlowable(items, bulletType="bullet", start=BULLETS[depth % 2], **options)

    def checklist(self, block: ListBlock, depth: int) -> PdfTable:
        rows = [
            [
                "" if item.checked is None else CheckBox(item.checked, self.styles.accent),
                self.flowables(item.blocks, depth + 1, nested=True) or "",
            ]
            for item in block.items
        ]
        table = PdfTable(
            rows,
            colWidths=[CHECKBOX_SIZE + 8, "*"],
            hAlign="LEFT",
            spaceAfter=BODY_SIZE * 0.4 if depth == 0 else 0,
        )
        # Nudge the box down so it lines up with the first line of its item.
        box_offset = (self.styles.list_item.leading - CHECKBOX_SIZE) / 2 - 0.5
        table.setStyle(
            TableStyle(
                [
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("LEFTPADDING", (0, 0), (-1, -1), 0),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                    ("TOPPADDING", (0, 0), (-1, -1), 0),
                    ("TOPPADDING", (0, 0), (0, -1), box_offset),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 1),
                ]
            )
        )
        return table

    def quote(self, blocks: tuple[Block, ...], depth: int) -> PdfTable:
        content = self.flowables(blocks, depth, nested=True) or [Spacer(0, 0)]
        return self._panel(content, bar=self.styles.secondary, bar_width=2, fill=None)

    def callout(self, block: Callout, depth: int) -> PdfTable:
        colours = {"note": self.styles.primary, "tip": self.styles.secondary}
        colour = colours.get(block.kind, self.styles.accent)
        label_style = ParagraphStyle(
            f"brand-callout-{block.kind}",
            parent=self.styles.callout_label,
            textColor=legible(colour, self.styles.body.textColor),
        )
        content = [
            PdfParagraph(block.kind.title(), label_style),
            *self.flowables(block.blocks, depth, nested=True),
        ]
        fill = tint(colour, 0.12, self.styles.background)
        return self._panel(content, bar=colour, bar_width=3, fill=fill)

    def table(self, block: Table) -> PdfTable:
        styles = self.styles
        columns = len(block.header)
        weights = [
            min(max(len(plain_text(row[col])) for row in (block.header, *block.rows)), 40) + 6
            for col in range(columns)
        ]
        widths = [f"{100 * weight / sum(weights):.3f}%" for weight in weights]

        def cell(content: tuple[Inline, ...], style: ParagraphStyle, align: str | None) -> Flowable:
            aligned = ParagraphStyle(
                f"{style.name}-{align}", parent=style, alignment=ALIGNMENTS[align]
            )
            return PdfParagraph(markup(content, styles), aligned)

        data = [
            [
                cell(c, styles.table_header, a)
                for c, a in zip(block.header, block.align, strict=True)
            ]
        ]
        data += [
            [cell(c, styles.table_cell, a) for c, a in zip(row, block.align, strict=True)]
            for row in block.rows
        ]
        table = PdfTable(
            data,
            colWidths=widths,
            repeatRows=1,
            hAlign="LEFT",
            spaceBefore=BODY_SIZE * 0.3,
            spaceAfter=BODY_SIZE,
        )
        table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), styles.primary),
                    ("ROWBACKGROUNDS", (0, 1), (-1, -1), [styles.background, styles.zebra]),
                    ("LINEBELOW", (0, 1), (-1, -1), 0.25, styles.secondary),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("LEFTPADDING", (0, 0), (-1, -1), CELL_PADDING + 1),
                    ("RIGHTPADDING", (0, 0), (-1, -1), CELL_PADDING + 1),
                    ("TOPPADDING", (0, 0), (-1, -1), CELL_PADDING - 1),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), CELL_PADDING),
                ]
            )
        )
        return table

    def image_path(self, block: Image) -> Path:
        if _REMOTE.match(block.src):
            raise DocumentError(
                [f"remote images are not supported ({block.src}); download it and use a local path"]
            )
        path = (self.base_dir / block.src).resolve()
        if path.suffix.lower() not in IMAGE_SUFFIXES:
            raise DocumentError([f"image '{block.src}' must be a .png, .jpg or .jpeg file"])
        if not path.is_file():
            raise DocumentError([f"image not found: {path}"])
        return path

    def _panel(
        self, content: list[Flowable], bar: Color, bar_width: float, fill: Color | None
    ) -> PdfTable:
        """A full-width box with a coloured bar down its left edge; it may split across pages."""
        panel = PdfTable(
            [[content]],
            colWidths=["100%"],
            splitInRow=1,
            spaceBefore=BODY_SIZE * 0.3,
            spaceAfter=BODY_SIZE,
        )
        commands = [
            ("LINEBEFORE", (0, 0), (0, -1), bar_width, bar),
            ("LEFTPADDING", (0, 0), (-1, -1), CELL_PADDING * 2),
            ("RIGHTPADDING", (0, 0), (-1, -1), CELL_PADDING * 2),
            ("TOPPADDING", (0, 0), (-1, -1), CELL_PADDING + 2),
            ("BOTTOMPADDING", (0, 0), (-1, -1), CELL_PADDING),
        ]
        if fill is not None:
            commands.append(("BACKGROUND", (0, 0), (-1, -1), fill))
        panel.setStyle(TableStyle(commands))
        return panel
