# brandpdf

Turn a brand kit and Markdown into consistently branded, multi-page PDFs.

Write your colours, fonts, logo and letterhead once in `brand.yaml`. Write documents in plain
Markdown. Run one command and get a PDF that looks like your organisation made it, every time.

<table>
<tr>
<td><a href="examples/fernleaf-studio/site-visit-checklist.pdf"><img src="https://raw.githubusercontent.com/faisal-pm/Branded-PDF-Generator/main/docs/images/fernleaf-studio.png" alt="Fernleaf Studio site visit checklist" width="260"></a></td>
<td><a href="examples/kestrel-labs/test-programme-report.pdf"><img src="https://raw.githubusercontent.com/faisal-pm/Branded-PDF-Generator/main/docs/images/kestrel-labs.png" alt="Kestrel Labs test programme report" width="260"></a></td>
<td><a href="examples/tidewell-health/appointment-letter.pdf"><img src="https://raw.githubusercontent.com/faisal-pm/Branded-PDF-Generator/main/docs/images/tidewell-health.png" alt="Tidewell Community Health appointment letter" width="260"></a></td>
</tr>
<tr>
<td>Generated letterhead, A4</td>
<td>Supplied PDF letterheads, A4</td>
<td>Supplied PNG letterhead, US Letter</td>
</tr>
</table>

All three brands are fictional. Each one is a `brand.yaml` plus a Markdown file in
[examples/](examples); the first page above comes from Markdown like this:

```markdown
---
title: Site Visit Checklist
subtitle: Garden renovation at 14 Orchard Row
reference: FS-SV-014
---

## Before the visit

- [x] Confirm access times with the homeowner
- [ ] Charge the laser level and camera

> [!WARNING]
> The rear boundary wall is unstable. Stay at least two metres from it.

| Bed | Plant | Qty |
|:--|:--|--:|
| A | Hakonechloa macra | 12 |
```

## Quickstart

You need Python 3.10 or newer.

```sh
pip install brandpdf
```

Create a brand kit, then open `brand.yaml` and change the name, colours and contact details:

```sh
brandpdf init
```

Write a document, say `hello.md`:

```markdown
---
title: Hello
reference: DOC-001
---

## First steps

- [x] Install brandpdf
- [ ] Make it yours

> [!TIP]
> Add `logo: logo.png` to brand.yaml to put your logo in the letterhead.
```

Build it:

```sh
brandpdf build hello.md
```

That writes `hello.pdf` beside `hello.md`, using `./brand.yaml`. Open it, adjust the kit, and run
the command again.

## What you get

- **One brand kit** for colours, fonts (built-in or your own `.ttf` files), logo, contact details,
  page size and margins. See the [brand kit reference](docs/brand-kit.md).
- **Letterheads** generated from the kit, or your own PDF or image behind every page, with a
  separate continuation-page letterhead if you have one.
- **"Page 2 of 5" footers** and an optional document reference.
- **Markdown with extras:** tables that repeat their header row across pages, checklists,
  callouts, images, and per-document front matter. See [writing documents](docs/writing-documents.md).
- **Clear errors.** Every problem in a brand kit or document is listed at once, in plain terms,
  with suggestions for typos.
- **Deterministic output.** The same Markdown and brand kit always produce a byte-identical PDF.

## Command line

```sh
brandpdf init [brand.yaml] [--force]       # write a starter brand kit
brandpdf build doc.md                      # ./brand.yaml -> doc.pdf
brandpdf build doc.md -b kit.yaml -o out.pdf
brandpdf build letters/ -o pdfs/           # every .md file in a folder
```

## Python

```python
from pathlib import Path

from brandpdf import load_brand, render

brand = load_brand("brand.yaml")
pdf = render(Path("doc.md").read_text(), brand, base_dir="docs")  # images resolve against docs/
Path("doc.pdf").write_bytes(pdf)
```

`render` raises `brandpdf.DocumentError` for problems in a document and `brandpdf.BrandError` for
problems in a kit; both carry a `problems` list.

## Development

Requires [uv](https://docs.astral.sh/uv/).

```sh
uv sync                                      # create the virtualenv with dev dependencies
uv run pytest                                # run the tests
BRANDPDF_UPDATE_SNAPSHOTS=1 uv run pytest    # accept new visual snapshots (check them first)
uv run python scripts/build_examples.py      # rebuild example PDFs and README images
```

Tests cover parsing, validation, the text and fonts in rendered PDFs, and visual snapshots of each
page compared within a small pixel tolerance.

## Licence

Apache-2.0. See [LICENSE](LICENSE). The fonts in [examples/fonts](examples/fonts) are under the
SIL Open Font License; each licence sits beside its font.
