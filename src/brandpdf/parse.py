"""Markdown to intermediate blocks (F6-F9).

The blocks are plain frozen dataclasses with no ReportLab types, so parsing can be tested on its
own and the layout layer only has to handle a small, fixed vocabulary.
"""

from __future__ import annotations

from dataclasses import dataclass, replace

from markdown_it import MarkdownIt
from markdown_it.tree import SyntaxTreeNode

# Raw HTML is disabled so tags arrive as literal text rather than being dropped.
_MARKDOWN = MarkdownIt("commonmark", {"html": False})


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


Block = Heading | Paragraph | ListBlock | CodeBlock | Quote | Rule


def parse(markdown: str) -> list[Block]:
    """Parse Markdown into a flat list of top-level blocks."""
    root = SyntaxTreeNode(_MARKDOWN.parse(markdown))
    return _blocks(root.children)


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
        return Paragraph(_inline(node.children[0]))
    if kind in ("bullet_list", "ordered_list"):
        items = tuple(ListItem(tuple(_blocks(item.children))) for item in node.children)
        start = int(node.attrs.get("start", 1))
        return ListBlock(ordered=kind == "ordered_list", items=items, start=start)
    if kind in ("fence", "code_block"):
        return CodeBlock(node.content.rstrip("\n"))
    if kind == "blockquote":
        return Quote(tuple(_blocks(node.children)))
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
