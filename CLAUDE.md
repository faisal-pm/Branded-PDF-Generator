# brandpdf: build conventions

Open-source Python library + CLI that turns a brand kit (`brand.yaml`) plus Markdown into
branded, multi-page PDFs on ReportLab Platypus. Public portfolio piece: code must read cleanly.

## Commands

- `uv sync`: install runtime and dev dependencies
- `uv run pytest`: run tests
- `BRANDPDF_UPDATE_SNAPSHOTS=1 uv run pytest`: accept current output as the new visual snapshots
  (a deliberate step: look at the new PNGs in `tests/snapshots/` before committing them)
- `uv run ruff check . && uv run ruff format .`: lint and format
- `uv run brandpdf --help`: run the CLI

## Architecture

Three layers, each testable on its own:

1. `parse.py`: Markdown (markdown-it-py) to a list of plain intermediate blocks. No ReportLab imports.
2. `flowables.py`: blocks to Platypus flowables, styled from the `Brand`.
3. `letterhead.py`: draws the letterhead and footer on each page via page-template callbacks.
   Image backgrounds are drawn by ReportLab; PDF backgrounds are merged underneath with pypdf.
   Footers ("Page 2 of 5") are drawn by `NumberedCanvas` once the page count is known.

`brand.py` holds the pydantic brand-kit model and loader. `errors.py` turns pydantic errors into
plain-language problems (`BrandError`, `DocumentError`). `render.py` exposes the public
`render(markdown, brand, *, base_dir=None) -> bytes`: it splits front matter, applies brand
overrides, and builds the page templates. `cli.py` is a thin Typer layer over `render`.

Layout gotchas: tables, checklists, quotes and callouts are ReportLab `Table`s (callouts and quotes
use `splitInRow=1` so they can break across pages). Headings use `CondPageBreak`, not
`keepWithNext`, which would drag a long table onto the next page with its heading.

## Rules

- Test first: every feature lands with a test that failed before the code was written.
- Output must be deterministic: same inputs, byte-identical PDF (fix creation dates and IDs).
- Python 3.10+, type hints throughout, no `Optional[...]`; use `X | None`.
- Keep the CLI thin; logic lives in the library.
- Clean-room: fictional brands only, SIL OFL fonts only. Never add real company names, logos,
  colours or documents, and never copy from any internal template library.
- Requirement IDs (F1–F15) refer to the PRD; cite them in module docstrings and tests.
