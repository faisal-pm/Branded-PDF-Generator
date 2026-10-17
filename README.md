# brandpdf

Turn a brand kit and Markdown into consistently branded, multi-page PDFs.

> **Status: pre-alpha.** Brand kits load and validate; rendering is not implemented yet.

## What it will do

Write `brand.yaml` once (colours, fonts, logo, letterhead, contact details), write documents in
Markdown, and run one command:

```sh
brandpdf build doc.md --brand brand.yaml -o out.pdf
```

Or from Python:

```python
from brandpdf import render

pdf_bytes = render(markdown_text, brand)
```

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
uv run brandpdf --help
```

## Licence

Apache-2.0. See [LICENSE](LICENSE).
