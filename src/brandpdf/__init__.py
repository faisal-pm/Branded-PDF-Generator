"""Turn a brand kit and Markdown into consistently branded, multi-page PDFs."""

from importlib.metadata import version

from brandpdf.render import render

__version__ = version("brandpdf")

__all__ = ["__version__", "render"]
