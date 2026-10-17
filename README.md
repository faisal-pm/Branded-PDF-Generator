# brandpdf

Turn a brand kit and Markdown into consistently branded, multi-page PDFs.

> **Status: pre-alpha.** The project skeleton is in place; rendering is not implemented yet.

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

## Development

Requires [uv](https://docs.astral.sh/uv/).

```sh
uv sync          # create the virtualenv and install dev dependencies
uv run pytest    # run the test suite
uv run brandpdf --help
```

## Licence

Apache-2.0. See [LICENSE](LICENSE).
