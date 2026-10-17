"""Command-line interface (F12, F14)."""

from __future__ import annotations

from pathlib import Path
from typing import Annotated

import typer

from brandpdf import __version__

app = typer.Typer(
    help="Turn a brand kit and Markdown into branded PDFs.",
    no_args_is_help=True,
    add_completion=False,
)


def _version_callback(value: bool) -> None:
    if value:
        typer.echo(f"brandpdf {__version__}")
        raise typer.Exit()


def _not_implemented(command: str) -> None:
    typer.echo(f"Error: 'brandpdf {command}' is not implemented yet.", err=True)
    raise typer.Exit(code=1)


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
    brand: Annotated[Path, typer.Option("--brand", "-b", help="Brand kit YAML file.")],
    output: Annotated[Path, typer.Option("--output", "-o", help="Output PDF path.")],
) -> None:
    """Render a Markdown document to a branded PDF."""
    _not_implemented("build")


@app.command()
def init(
    path: Annotated[Path, typer.Argument(help="Where to write the brand kit.")] = Path(
        "brand.yaml"
    ),
) -> None:
    """Scaffold a starter brand kit."""
    _not_implemented("init")
