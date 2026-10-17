"""Markdown to intermediate blocks (F6)."""

from brandpdf.parse import (
    CodeBlock,
    Heading,
    LineBreak,
    ListBlock,
    ListItem,
    Paragraph,
    Quote,
    Rule,
    Text,
    parse,
)


def para(*spans: Text | LineBreak) -> Paragraph:
    return Paragraph(spans)


def item(*blocks: object) -> ListItem:
    return ListItem(blocks)  # type: ignore[arg-type]


def test_headings_keep_their_level() -> None:
    assert parse("# One\n\n## Two\n\n### Three\n\n#### Four") == [
        Heading(1, (Text("One"),)),
        Heading(2, (Text("Two"),)),
        Heading(3, (Text("Three"),)),
        Heading(4, (Text("Four"),)),
    ]


def test_inline_styles_become_styled_spans() -> None:
    blocks = parse("Plain **bold** *italic* `x < y` [site](https://fernleaf.example)")

    assert blocks == [
        para(
            Text("Plain "),
            Text("bold", bold=True),
            Text(" "),
            Text("italic", italic=True),
            Text(" "),
            Text("x < y", code=True),
            Text(" "),
            Text("site", href="https://fernleaf.example"),
        )
    ]


def test_nested_emphasis_combines_styles() -> None:
    assert parse("***both*** and **[bold link](https://a.example)**") == [
        para(
            Text("both", bold=True, italic=True),
            Text(" and "),
            Text("bold link", bold=True, href="https://a.example"),
        )
    ]


def test_soft_breaks_join_lines_and_hard_breaks_are_kept() -> None:
    assert parse("one\ntwo  \nthree") == [para(Text("one two"), LineBreak(), Text("three"))]


def test_bullet_list() -> None:
    assert parse("- Read the notes\n- Sign in") == [
        ListBlock(
            ordered=False,
            items=(item(para(Text("Read the notes"))), item(para(Text("Sign in")))),
        )
    ]


def test_ordered_list_keeps_its_start_number() -> None:
    assert parse("3. Third\n4. Fourth") == [
        ListBlock(
            ordered=True,
            start=3,
            items=(item(para(Text("Third"))), item(para(Text("Fourth")))),
        )
    ]


def test_nested_list_sits_inside_its_parent_item() -> None:
    blocks = parse("- Sign in\n  - Collect a badge\n- Leave")

    assert blocks == [
        ListBlock(
            ordered=False,
            items=(
                item(
                    para(Text("Sign in")),
                    ListBlock(ordered=False, items=(item(para(Text("Collect a badge"))),)),
                ),
                item(para(Text("Leave"))),
            ),
        )
    ]


def test_code_rule_and_quote() -> None:
    assert parse("```\nx < y\n  indented\n```\n\n---\n\n> Quoted **text**") == [
        CodeBlock("x < y\n  indented"),
        Rule(),
        Quote((para(Text("Quoted "), Text("text", bold=True)),)),
    ]


def test_raw_html_is_treated_as_text() -> None:
    assert parse("<div>raw</div>\n\nSay <b>hi</b>") == [
        para(Text("<div>raw</div>")),
        para(Text("Say <b>hi</b>")),
    ]


def test_empty_document_has_no_blocks() -> None:
    assert parse("") == []
    assert parse("\n\n   \n") == []
