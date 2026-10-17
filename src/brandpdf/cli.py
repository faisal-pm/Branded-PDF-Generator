"""Command-line interface (F12, F14)."""

from __future__ import annotations

from pathlib import Path
from typing import Annotated

import typer

from brandpdf import __version__
from brandpdf.brand import BrandError, load_brand, starter_kit
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
    source: Annotated[Path, typer.Argument(help="Markdown file to render.")],
    brand: Annotated[Path, typer.Option("--brand", "-b", help="Brand kit YAML file.")] = Path(
        "brand.yaml"
    ),
    output: Annotated[
        Path | None,
        typer.Option("--output", "-o", help="Output PDF path. Defaults to the source with .pdf."),
    ] = None,
) -> None:
    """Render a Markdown document to a branded PDF."""
    try:
        kit = load_brand(brand)
    except BrandError as exc:
        raise _fail(str(exc)) from None
    try:
        markdown = source.read_text(encoding="utf-8")
    except FileNotFoundError:
        raise _fail(f"Error: document not found: {source}") from None

    target = output or source.with_suffix(".pdf")
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(render(markdown, kit))
    typer.echo(f"Wrote {target}")


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
    typer.echo(f"Edit it, then run: brandpdf build doc.md --brand {path} -o out.pdf")
