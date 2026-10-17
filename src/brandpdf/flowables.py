"""Blocks to Platypus flowables, including checklist and callout styles.

Every visual decision (sizes, spacing, which brand colour goes where) lives in ``build_styles``,
so the mapping from blocks to flowables stays a plain translation.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path
from xml.sax.saxutils import escape

from reportlab.lib.colors import Color, HexColor
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    Flowable,
    HRFlowable,
    Indenter,
    ListFlowable,
    Preformatted,
    Spacer,
)
from reportlab.platypus import ListItem as PdfListItem
from reportlab.platypus import Paragraph as PdfParagraph

from brandpdf.brand import Brand
from brandpdf.parse import (
    Block,
    CodeBlock,
    Heading,
    Inline,
    LineBreak,
    ListBlock,
    Paragraph,
    Quote,
    Rule,
)

BODY_SIZE = 10.5
HEADING_SIZES = {1: 22.0, 2: 16.0, 3: 13.0}  # deeper headings use the level 3 style
CODE_FONT = "Courier"
BULLETS = ("•", "–")  # alternate by nesting depth
LIST_INDENT = 16.0
QUOTE_INDENT = 14.0


@dataclass(frozen=True)
class Styles:
    body: ParagraphStyle
    list_item: ParagraphStyle
    headings: dict[int, ParagraphStyle]
    code: ParagraphStyle
    accent: Color
    rule: Color
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


def build_styles(brand: Brand) -> Styles:
    colors = brand.colors
    body = ParagraphStyle(
        "brand-body",
        fontName=register_font(brand.fonts.body),
        fontSize=BODY_SIZE,
        leading=BODY_SIZE * 1.4,
        textColor=HexColor(colors.text),
        spaceAfter=BODY_SIZE * 0.6,
    )
    heading_font = register_font(brand.fonts.heading)
    headings = {
        level: ParagraphStyle(
            f"brand-h{level}",
            parent=body,
            fontName=heading_font,
            fontSize=size,
            leading=size * 1.25,
            textColor=HexColor(colors.primary),
            spaceBefore=size * 0.9,
            spaceAfter=size * 0.4,
            keepWithNext=True,
        )
        for level, size in HEADING_SIZES.items()
    }
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
        accent=HexColor(colors.accent),
        rule=HexColor(colors.secondary),
        link=colors.primary,
    )


def to_flowables(blocks: list[Block] | tuple[Block, ...], styles: Styles) -> list[Flowable]:
    return _flowables(blocks, styles, depth=0, in_list=False)


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


def _flowables(
    blocks: list[Block] | tuple[Block, ...], styles: Styles, depth: int, in_list: bool
) -> list[Flowable]:
    out: list[Flowable] = []
    for block in blocks:
        match block:
            case Heading(level=level, content=content):
                style = styles.headings[min(level, max(HEADING_SIZES))]
                out.append(PdfParagraph(markup(content, styles), style))
            case Paragraph(content=content):
                style = styles.list_item if in_list else styles.body
                out.append(PdfParagraph(markup(content, styles), style))
            case ListBlock():
                out.append(_list(block, styles, depth))
            case CodeBlock(text=text):
                out.append(Preformatted(text, styles.code))
            case Quote(blocks=children):
                out.append(Indenter(left=QUOTE_INDENT))
                out.extend(_flowables(children, styles, depth, in_list))
                out.append(Indenter(left=-QUOTE_INDENT))
            case Rule():
                out.append(
                    HRFlowable(
                        width="100%",
                        thickness=0.75,
                        color=styles.rule,
                        spaceBefore=BODY_SIZE * 0.4,
                        spaceAfter=BODY_SIZE,
                    )
                )
    return out


def _list(block: ListBlock, styles: Styles, depth: int) -> ListFlowable:
    items = [
        PdfListItem(_flowables(item.blocks, styles, depth + 1, in_list=True) or [Spacer(0, 0)])
        for item in block.items
    ]
    options = {
        "leftIndent": LIST_INDENT,
        "bulletColor": styles.accent,
        "bulletFontName": styles.body.fontName,
        "bulletFontSize": styles.body.fontSize,
        "spaceAfter": BODY_SIZE * 0.4 if depth == 0 else 0,
    }
    if block.ordered:
        return ListFlowable(items, bulletType="1", start=block.start, bulletFormat="%s.", **options)
    bullet = BULLETS[depth % len(BULLETS)]
    return ListFlowable(items, bulletType="bullet", start=bullet, **options)
