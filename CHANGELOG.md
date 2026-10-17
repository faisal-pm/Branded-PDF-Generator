# Changelog

All notable changes to brandpdf are listed here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and versions follow
[Semantic Versioning](https://semver.org/).

## [1.0.0] - Unreleased

First public release.

### Added

- Brand kit (`brand.yaml`): colours, fonts (built-in or TrueType), logo, contact details, page
  size and margins, validated on load with every problem listed in plain terms.
- `brandpdf init` to scaffold a commented starter kit.
- Markdown rendering: headings, paragraphs, emphasis, links, code, bullet and numbered lists,
  rules, quotes, block images.
- Tables with column alignment and header rows that repeat across pages.
- Checklists (`- [ ]`, `- [x]`) with branded tick boxes.
- Callouts using GitHub alert syntax (`[!NOTE]`, `[!TIP]`, `[!WARNING]`).
- YAML front matter for a title block, footer reference and per-document brand overrides.
- Letterheads generated from the brand kit, or supplied as PDF, PNG or JPEG, with separate
  first-page and continuation-page files.
- "Page X of Y" footers.
- `brandpdf build` for one document or a folder of them; Python API `render()`.
- Deterministic output: the same inputs give a byte-identical PDF.
- Three fictional example brands with sample documents and output PDFs.

[1.0.0]: https://github.com/faisal-pm/Branded-PDF-Generator/releases/tag/v1.0.0
