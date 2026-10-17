# Writing documents

Documents are plain Markdown ([CommonMark](https://commonmark.org)) with a few extras for
checklists, callouts, tables and per-document settings. Raw HTML is shown as text, not
interpreted.

## Front matter

An optional YAML block at the very top sets details for this document only:

```markdown
---
title: Site Visit Checklist
subtitle: Garden renovation at 14 Orchard Row
date: 2026-10-21
reference: FS-SV-014
brand:
  colors:
    primary: "#7A1F3D"
---
```

| Key | What it does |
|:--|:--|
| `title` | Large title at the top of page 1, the PDF title, and the continuation-page header. |
| `subtitle` | A line under the title. |
| `date` | Shown under the title, as written. |
| `reference` | Shown under the title and before the page number in every footer. |
| `brand` | Any brand kit keys, merged over the kit for this document and validated the same way. |

Without front matter, the PDF title comes from the first `#` heading, or the brand name.

## Text

| You write | You get |
|:--|:--|
| `# Heading` to `### Heading` | Headings in the heading font and primary colour; deeper levels look like `###`. |
| `**bold**`, `*italic*` | Bold and italic (see the note on single-file fonts in the [brand kit reference](brand-kit.md#fonts)). |
| `` `code` `` | Inline code in Courier. |
| `[text](https://…)` | A clickable link in the primary colour. |
| Two spaces at a line end | A line break inside a paragraph. |
| `---` on its own line | A horizontal rule. |
| Fenced code block | Monospaced text, kept exactly as written. |

## Lists and checklists

```markdown
- Bullet item
  - Nested item
1. Numbered item

- [ ] Open task
- [x] Done task
```

Bullets and numbers use the accent colour. A list whose items start with `[ ]` or `[x]` becomes a
checklist with tick boxes instead of bullets.

## Callouts and quotes

```markdown
> [!NOTE]
> The site office opens at 7am.

> [!TIP]
> Bring a water bottle.

> [!WARNING]
> Hard hats are required beyond the gate.
```

Callouts use GitHub's alert syntax and render as tinted panels: note in the primary colour, tip in
the secondary, warning in the accent. Any other `>` quote gets a plain bar down its left edge.
Long callouts and quotes continue onto the next page.

## Tables

```markdown
| Bed | Plant | Qty |
|:--|:--|--:|
| A | Hakonechloa macra | 12 |
```

The header row is filled with the primary colour and repeats at the top of every page the table
spans. `:--`, `:-:` and `--:` align a column left, centre or right. Column widths follow the
length of their content.

## Images

```markdown
![Site plan](images/site-plan.png)
```

An image on its own line is placed at its natural size (assuming 96 dpi), shrunk to fit the column
and page if needed. Paths are relative to the Markdown file. PNG and JPEG are supported; remote
URLs are not, so download the image first. An image inside a sentence is replaced by its alt text.
