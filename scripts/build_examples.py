"""Rebuild the example PDFs and the README preview images.

Run from the repo root after changing the renderer or an example:

    uv run python scripts/build_examples.py

Each folder in examples/ holds a brand.yaml and one or more .md documents. Every document is
rendered next to its source, and the first page of each is saved to docs/images/ for the README.
"""

from __future__ import annotations

from pathlib import Path

import pymupdf

from brandpdf import load_brand, render

ROOT = Path(__file__).resolve().parent.parent
PREVIEW_DPI = 80


def main() -> None:
    images = ROOT / "docs" / "images"
    images.mkdir(parents=True, exist_ok=True)
    for kit in sorted((ROOT / "examples").glob("*/brand.yaml")):
        brand = load_brand(kit)
        for source in sorted(kit.parent.glob("*.md")):
            pdf = render(source.read_text(encoding="utf-8"), brand, base_dir=source.parent)
            source.with_suffix(".pdf").write_bytes(pdf)
            with pymupdf.open(stream=pdf, filetype="pdf") as document:
                preview = images / f"{kit.parent.name}.png"
                document[0].get_pixmap(dpi=PREVIEW_DPI).save(preview)
                print(f"{source.relative_to(ROOT)}: {len(document)} page(s) -> {preview.name}")


if __name__ == "__main__":
    main()
