"""Markdown to intermediate blocks (F6-F9).

The blocks are plain frozen dataclasses with no ReportLab types, so parsing can be tested on its
own and the layout layer only has to handle a small, fixed vocabulary.

Beyond CommonMark, three conventions are recognised:

- Tables (GitHub style, with ``:--:`` alignment markers).
- Checklists: list items starting ``[ ]`` or ``[x]`` (F7).
- Callouts: GitHub alert quotes starting ``[!NOTE]``, ``[!TIP]`` or ``[!WARNING]`` (F8).

A document may open with YAML front matter between ``---`` lines (F9).
"""

from __future__ import annotations

import datetime
import re
from collections.abc import Mapping
from dataclasses import dataclass, field, replace
from typing import Any

import yaml
from markdown_it import MarkdownIt
from markdown_it.tree import SyntaxTreeNode
from pydantic import BaseModel, ConfigDict, ValidationError, field_validator

from brandpdf.errors import DocumentError, describe

# Raw HTML is disabled so tags arrive as literal text rather than being dropped.
_MARKDOWN = MarkdownIt("commonmark", {"html": False}).enable("table")

CALLOUT_KINDS = ("note", "tip", "warning")
_CALLOUT = re.compile(r"\[!(note|tip|warning)\]\s*", re.IGNORECASE)
_CHECKBOX = re.compile(r"\[([ xX])\](?: |$)")
_ALIGN = re.compile(r"text-align:\s*(left|center|right)")
# The opening line must be followed by content, so a leading horizontal rule is left alone.
_FRONT_MATTER = re.compile(
    r"\A---[ \t]*\r?\n(?=\S)(.*?)^(?:---|\.\.\.)[ \t]*(?:\r?\n|\Z)", re.DOTALL | re.MULTILINE
)


@dataclass(frozen=True)
class Text:
    """A run of text sharing one style."""

    text: str
    bold: bool = False
    italic: bool = False
    code: bool = False
    href: str | None = None


@dataclass(frozen=True)
class LineBreak:
    """A hard line break inside a paragraph."""


Inline = Text | LineBreak


@dataclass(frozen=True)
class Heading:
    level: int
    content: tuple[Inline, ...]


@dataclass(frozen=True)
class Paragraph:
    content: tuple[Inline, ...]


@dataclass(frozen=True)
class ListItem:
    blocks: tuple[Block, ...]
    checked: bool | None = None  # True or False for a checklist item, None for a plain one


@dataclass(frozen=True)
class ListBlock:
    ordered: bool
    items: tuple[ListItem, ...]
    start: int = 1


@dataclass(frozen=True)
class CodeBlock:
    text: str


@dataclass(frozen=True)
class Quote:
    blocks: tuple[Block, ...]


@dataclass(frozen=True)
class Rule:
    """A horizontal rule."""


Cell = tuple[Inline, ...]


@dataclass(frozen=True)
class Table:
    header: tuple[Cell, ...]
    rows: tuple[tuple[Cell, ...], ...]
    align: tuple[str | None, ...]  # "left", "center", "right" or None per column


@dataclass(frozen=True)
class Callout:
    kind: str  # one of CALLOUT_KINDS
    blocks: tuple[Block, ...]


@dataclass(frozen=True)
class Image:
    """An image on its own line. ``src`` is left unresolved; layout resolves and checks it."""

    src: str
    alt: str


Block = Heading | Paragraph | ListBlock | CodeBlock | Quote | Rule | Table | Callout | Image


class FrontMatter(BaseModel):
    """Per-document settings from the YAML block at the top of a document (F9)."""

    model_config = ConfigDict(extra="forbid", frozen=True, coerce_numbers_to_str=True)

    title: str | None = None
    subtitle: str | None = None
    date: str | None = None
    reference: str | None = None
    brand: dict[str, Any] = {}  # brand kit keys that override the kit for this document

    @field_validator("date", mode="before")
    @classmethod
    def _date(cls, value: Any) -> Any:
        return value.isoformat() if isinstance(value, datetime.date) else value

    @field_validator("brand", mode="before")
    @classmethod
    def _brand(cls, value: Any) -> dict[str, Any]:
        if value is None:
            return {}
        if not isinstance(value, Mapping):
            raise ValueError(
                f"expected a section of brand kit keys (name, colors, fonts, ...), got {value!r}"
            )
        return dict(value)


@dataclass(frozen=True)
class Document:
    meta: FrontMatter
    blocks: list[Block] = field(default_factory=list)


def parse(markdown: str) -> list[Block]:
    """Parse Markdown into a flat list of top-level blocks."""
    root = SyntaxTreeNode(_MARKDOWN.parse(markdown))
    return _blocks(root.children)


def parse_document(markdown: str) -> Document:
    """Split off and validate any front matter, then parse the body."""
    match = _FRONT_MATTER.match(markdown)
    if match is None:
        return Document(FrontMatter(), parse(markdown))
    return Document(_front_matter(match.group(1)), parse(markdown[match.end() :]))


def plain_text(content: tuple[Inline, ...]) -> str:
    """The text of some inline content with all styling dropped."""
    return "".join(span.text if isinstance(span, Text) else "\n" for span in content)


def _blocks(nodes: list[SyntaxTreeNode]) -> list[Block]:
    blocks: list[Block] = []
    for node in nodes:
        block = _block(node)
        if block is not None:
            blocks.append(block)
    return blocks


def _block(node: SyntaxTreeNode) -> Block | None:
    kind = node.type
    if kind == "heading":
        return Heading(int(node.tag[1]), _inline(node.children[0]))
    if kind == "paragraph":
        return _lone_image(node.children[0]) or Paragraph(_inline(node.children[0]))
    if kind in ("bullet_list", "ordered_list"):
        items = tuple(_list_item(item) for item in node.children)
        start = int(node.attrs.get("start", 1))
        return ListBlock(ordered=kind == "ordered_list", items=items, start=start)
    if kind in ("fence", "code_block"):
        return CodeBlock(node.content.rstrip("\n"))
    if kind == "blockquote":
        blocks = _blocks(node.children)
        return _callout(blocks) or Quote(tuple(blocks))
    if kind == "table":
        return _table(node)
    if kind == "hr":
        return Rule()
    if kind == "html_block":  # only reached if HTML parsing is ever re-enabled
        return Paragraph((Text(node.content.strip()),))
    return None


def _inline(node: SyntaxTreeNode) -> tuple[Inline, ...]:
    spans: list[Inline] = []
    _collect(node.children, Text(""), spans)
    return tuple(_merge(spans))


def _collect(nodes: list[SyntaxTreeNode], style: Text, out: list[Inline]) -> None:
    """Walk inline nodes depth-first; ``style`` carries the formatting of the enclosing nodes."""
    for node in nodes:
        kind = node.type
        if kind in ("text", "html_inline"):
            out.append(replace(style, text=node.content))
        elif kind == "softbreak":
            out.append(replace(style, text=" "))
        elif kind == "hardbreak":
            out.append(LineBreak())
        elif kind == "code_inline":
            out.append(replace(style, text=node.content, code=True))
        elif kind == "strong":
            _collect(node.children, replace(style, bold=True), out)
        elif kind == "em":
            _collect(node.children, replace(style, italic=True), out)
        elif kind == "link":
            _collect(node.children, replace(style, href=str(node.attrs["href"])), out)
        else:  # images and anything newer: keep their text (an image's alt text) for now
            _collect(node.children, style, out)


def _merge(spans: list[Inline]) -> list[Inline]:
    """Join neighbouring runs that share a style, so "one" + " " + "two" becomes "one two"."""
    merged: list[Inline] = []
    for span in spans:
        if isinstance(span, Text) and not span.text:
            continue
        previous = merged[-1] if merged else None
        if (
            isinstance(span, Text)
            and isinstance(previous, Text)
            and replace(previous, text="") == replace(span, text="")
        ):
            merged[-1] = replace(previous, text=previous.text + span.text)
        else:
            merged.append(span)
    return merged


def _front_matter(text: str) -> FrontMatter:
    try:
        data = yaml.safe_load(text)
    except yaml.YAMLError as exc:
        mark = getattr(exc, "problem_mark", None)
        # +2: lines count from 1, and the opening --- is the first line of the file
        where = f" at line {mark.line + 2}" if mark else ""
        problem = getattr(exc, "problem", None) or "could not be parsed"
        raise DocumentError([f"front matter is not valid YAML{where}: {problem}"]) from None
    if data is None:
        data = {}
    if not isinstance(data, Mapping):
        raise DocumentError(["front matter must be keys such as 'title' and 'reference'"])
    try:
        return FrontMatter.model_validate(data)
    except ValidationError as exc:
        problems = [f"front matter: {describe(error, FrontMatter)}" for error in exc.errors()]
        raise DocumentError(problems) from None


def _list_item(node: SyntaxTreeNode) -> ListItem:
    blocks = _blocks(node.children)
    match, content = _leading_marker(blocks, _CHECKBOX)
    if match is None:
        return ListItem(tuple(blocks))
    body = ([Paragraph(content)] if content else []) + blocks[1:]
    return ListItem(tuple(body), checked=match.group(1) != " ")


def _callout(blocks: list[Block]) -> Callout | None:
    match, content = _leading_marker(blocks, _CALLOUT)
    if match is None:
        return None
    body = ([Paragraph(content)] if content else []) + blocks[1:]
    return Callout(match.group(1).lower(), tuple(body))


def _leading_marker(
    blocks: list[Block], pattern: re.Pattern[str]
) -> tuple[re.Match[str] | None, tuple[Inline, ...]]:
    """Match ``pattern`` at the start of the first paragraph; return it and what follows it."""
    first = blocks[0] if blocks else None
    if not (isinstance(first, Paragraph) and first.content and isinstance(first.content[0], Text)):
        return None, ()
    head = first.content[0]
    match = pattern.match(head.text)
    if match is None:
        return None, ()
    rest = head.text[match.end() :]
    content = ((replace(head, text=rest),) if rest else ()) + first.content[1:]
    while content and isinstance(content[0], LineBreak):
        content = content[1:]
    return match, content


def _lone_image(inline: SyntaxTreeNode) -> Image | None:
    """An image that is the only thing in its paragraph becomes an image block."""
    nodes = [
        child
        for child in inline.children
        if child.type != "softbreak" and not (child.type == "text" and not child.content.strip())
    ]
    if len(nodes) != 1 or nodes[0].type != "image":
        return None
    image = nodes[0]
    return Image(str(image.attrs["src"]), plain_text(_inline(image)))


def _table(node: SyntaxTreeNode) -> Table:
    head, *bodies = node.children
    header_row = head.children[0]

    def cells(row: SyntaxTreeNode) -> tuple[Cell, ...]:
        return tuple(_inline(cell.children[0]) if cell.children else () for cell in row.children)

    def align(cell: SyntaxTreeNode) -> str | None:
        match = _ALIGN.search(str(cell.attrs.get("style", "")))
        return match.group(1) if match else None

    return Table(
        header=cells(header_row),
        rows=tuple(cells(row) for body in bodies for row in body.children),
        align=tuple(align(cell) for cell in header_row.children),
    )
