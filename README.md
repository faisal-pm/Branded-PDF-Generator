# brandpdf

Turn a brand kit and Markdown into consistently branded, multi-page PDFs.

> **Status: pre-alpha.** Feature-complete for v1 (letterheads, page numbers, tables, checklists,
> callouts, images, front matter); examples and full docs are next.

## Usage

Write `brand.yaml` once (colours, fonts, logo, letterhead, contact details), write documents in
Markdown, and run one command:

```sh
brandpdf build doc.md --brand brand.yaml -o out.pdf
brandpdf build doc.md     # uses ./brand.yaml and writes doc.pdf
```

Or from Python:

```python
from pathlib import Path

from brandpdf import load_brand, render

pdf_bytes = render(Path("doc.md").read_text(), load_brand("brand.yaml"))
```

The same Markdown and brand kit always produce a byte-identical PDF.

## Brand kit

Create a commented starter kit, then edit it:

```sh
brandpdf init            # writes ./brand.yaml (use --force to overwrite)
```

```yaml
name: Fernleaf Studio
colors:                   # quote hex colours: a bare # starts a YAML comment
  primary: "#2E5E4E"
  secondary: "#8FB9A8"
  accent: "#F4A259"
fonts:                    # built-in PDF font or a .ttf path
  heading: fonts/Heading.ttf
  body: Helvetica
logo: logo.png
page:
  size: A4                # A4, A5, Letter or Legal
  margins_mm: {top: 25, right: 20, bottom: 25, left: 20}
```

Paths are relative to the kit file. Mistakes are reported all at once, in plain terms:

```text
Invalid brand kit brand.yaml:
  - colors.primary: '#2E5E4' is not a hex colour (expected "#RRGGBB" or "#RGB")
  - fonts.heading: file not found: /work/fonts/Heading.ttf
  - unknown key 'logo_path' (did you mean 'logo'?)
```

Load a kit from Python with `brandpdf.load_brand("brand.yaml")`.

## Development

Requires [uv](https://docs.astral.sh/uv/).

```sh
uv sync          # create the virtualenv and install dev dependencies
uv run pytest    # run the test suite
BRANDPDF_UPDATE_SNAPSHOTS=1 uv run pytest   # accept new visual snapshots
uv run brandpdf --help
```

## Licence

Apache-2.0. See [LICENSE](LICENSE).
