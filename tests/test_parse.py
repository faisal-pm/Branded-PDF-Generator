"""Markdown to intermediate blocks (F6)."""

import pytest

from brandpdf.errors import DocumentError
from brandpdf.parse import (
    Callout,
    CodeBlock,
    FrontMatter,
    Heading,
    Image,
    LineBreak,
    ListBlock,
    ListItem,
    Paragraph,
    Quote,
    Rule,
    Table,
    Text,
    parse,
    parse_document,
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


# Rich blocks (F6-F9)


def test_table_keeps_header_rows_and_alignment() -> None:
    blocks = parse(
        "| Item | Qty | Note |\n|:--|--:|:-:|\n| Boots | 2 | **new** |\n| Gloves | 10 | |"
    )

    assert blocks == [
        Table(
            header=((Text("Item"),), (Text("Qty"),), (Text("Note"),)),
            rows=(
                ((Text("Boots"),), (Text("2"),), (Text("new", bold=True),)),
                ((Text("Gloves"),), (Text("10"),), ()),
            ),
            align=("left", "right", "center"),
        )
    ]


def test_table_without_alignment_markers() -> None:
    [table] = parse("| A | B |\n|---|---|\n| 1 | 2 |")

    assert isinstance(table, Table)
    assert table.align == (None, None)


def test_task_list_items_carry_their_tick_state() -> None:
    assert parse("- [ ] Sign in\n- [x] Read the **notes**\n- [X] Park\n- Plain item") == [
        ListBlock(
            ordered=False,
            items=(
                ListItem((para(Text("Sign in")),), checked=False),
                ListItem((para(Text("Read the "), Text("notes", bold=True)),), checked=True),
                ListItem((para(Text("Park")),), checked=True),
                ListItem((para(Text("Plain item")),)),
            ),
        )
    ]


def test_brackets_without_a_space_are_not_a_checkbox() -> None:
    [block] = parse("- [x]ray results")

    assert isinstance(block, ListBlock)
    assert block.items[0].checked is None


def test_callouts_use_github_alert_syntax() -> None:
    assert parse("> [!WARNING]\n> Wear boots on site.\n\n> [!tip] Bring water.") == [
        Callout("warning", (para(Text("Wear boots on site.")),)),
        Callout("tip", (para(Text("Bring water.")),)),
    ]


def test_callout_body_can_hold_several_blocks() -> None:
    assert parse("> [!NOTE]\n>\n> First.\n>\n> - one") == [
        Callout(
            "note",
            (
                para(Text("First.")),
                ListBlock(ordered=False, items=(item(para(Text("one"))),)),
            ),
        )
    ]


def test_unknown_alert_type_stays_a_quote() -> None:
    assert parse("> [!DANGER] Careful") == [Quote((para(Text("[!DANGER] Careful")),))]


def test_image_on_its_own_line_is_an_image_block() -> None:
    assert parse("![Site map](images/map.png)") == [Image("images/map.png", "Site map")]


def test_image_inside_text_keeps_its_alt_text() -> None:
    assert parse("See the ![map](map.png) first.") == [para(Text("See the map first."))]


def test_front_matter_is_split_from_the_body() -> None:
    document = parse_document(
        "---\n"
        "title: Site Safety Induction\n"
        "subtitle: For contractors\n"
        "date: 2026-10-17\n"
        "reference: FS-SAF-001\n"
        "brand:\n"
        "  colors:\n"
        '    primary: "#123456"\n'
        "---\n"
        "# Welcome\n"
    )

    assert document.meta.title == "Site Safety Induction"
    assert document.meta.subtitle == "For contractors"
    assert document.meta.date == "2026-10-17"
    assert document.meta.reference == "FS-SAF-001"
    assert document.meta.brand == {"colors": {"primary": "#123456"}}
    assert document.blocks == [Heading(1, (Text("Welcome"),))]


def test_document_without_front_matter() -> None:
    document = parse_document("# Welcome")

    assert document.meta == FrontMatter()
    assert document.blocks == [Heading(1, (Text("Welcome"),))]


def test_leading_rule_is_not_mistaken_for_front_matter() -> None:
    document = parse_document("---\n\nAfter a rule")

    assert document.meta == FrontMatter()
    assert document.blocks == [Rule(), para(Text("After a rule"))]


@pytest.mark.parametrize(
    ("front_matter", "expected"),
    [
        ("titel: Oops\n", "front matter: unknown key 'titel' (did you mean 'title'?)"),
        ("title: [unclosed\n", "front matter is not valid YAML at line 3"),
        ("- a list\n", "front matter must be keys such as 'title' and 'reference'"),
        ("title: 12\nbrand: blue\n", "front matter: brand: expected a section of brand kit keys"),
    ],
)
def test_bad_front_matter_gives_a_readable_error(front_matter: str, expected: str) -> None:
    with pytest.raises(DocumentError) as excinfo:
        parse_document(f"---\n{front_matter}---\nBody")

    assert expected in str(excinfo.value)
