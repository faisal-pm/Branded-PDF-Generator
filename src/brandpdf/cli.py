"""Command-line interface (F12, F14): a thin layer over ``load_brand`` and ``render``."""

from __future__ import annotations

from pathlib import Path
from typing import Annotated

import typer

from brandpdf import __version__
from brandpdf.brand import Brand, BrandError, load_brand, starter_kit
from brandpdf.errors import DocumentError
from brandpdf.render import render

app = typer.Typer(
    help="Turn a brand kit and Markdown into branded PDFs.",
    no_args_is_help=True,
    add_completion=False,
)


def _version_callback(value: bool) -> None:
    if value:
        typer.echo(f"brandpdf {__version__}")
        raise typer.Exit()


def _fail(message: str) -> typer.Exit:
    typer.echo(message, err=True)
    return typer.Exit(code=1)


@app.callback()
def main(
    version: Annotated[
        bool | None,
        typer.Option(
            "--version",
            callback=_version_callback,
            is_eager=True,
            help="Show the version and exit.",
        ),
    ] = None,
) -> None:
    """Turn a brand kit and Markdown into branded PDFs."""


@app.command()
def build(
    source: Annotated[Path, typer.Argument(help="Markdown file to render, or a folder of them.")],
    brand: Annotated[Path, typer.Option("--brand", "-b", help="Brand kit YAML file.")] = Path(
        "brand.yaml"
    ),
    output: Annotated[
        Path | None,
        typer.Option(
            "--output",
            "-o",
            help="Output PDF, or output folder when SOURCE is a folder. "
            "Defaults to beside the source.",
        ),
    ] = None,
) -> None:
    """Render Markdown to branded PDFs."""
    try:
        kit = load_brand(brand)
    except BrandError as exc:
        raise _fail(str(exc)) from None

    if source.is_dir():
        documents = sorted(source.glob("*.md"))
        if not documents:
            raise _fail(f"Error: no .md files in {source}")
        folder = output or source
        results = [_build_one(doc, kit, folder / f"{doc.stem}.pdf") for doc in documents]
        if not all(results):
            raise typer.Exit(code=1)
        return

    if not source.is_file():
        raise _fail(f"Error: document not found: {source}")
    if not _build_one(source, kit, output or source.with_suffix(".pdf")):
        raise typer.Exit(code=1)


def _build_one(source: Path, kit: Brand, target: Path) -> bool:
    """Render one document, reporting problems against its file name. True on success."""
    try:
        pdf = render(source.read_text(encoding="utf-8"), kit, base_dir=source.parent)
    except DocumentError as exc:
        typer.echo(str(DocumentError(exc.problems, str(source))), err=True)
        return False
    except BrandError as exc:
        typer.echo(f"{source}: {exc}", err=True)
        return False
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(pdf)
    typer.echo(f"Wrote {target}")
    return True


@app.command()
def init(
    path: Annotated[Path, typer.Argument(help="Where to write the brand kit.")] = Path(
        "brand.yaml"
    ),
    force: Annotated[
        bool, typer.Option("--force", "-f", help="Overwrite an existing file.")
    ] = False,
) -> None:
    """Scaffold a starter brand kit."""
    if path.exists() and not force:
        raise _fail(f"Error: {path} already exists. Use --force to overwrite it.")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(starter_kit(), encoding="utf-8")
    typer.echo(f"Wrote starter brand kit to {path}")
    brand_option = "" if path == Path("brand.yaml") else f" --brand {path}"
    typer.echo(f"Edit it, then run: brandpdf build doc.md{brand_option}")
