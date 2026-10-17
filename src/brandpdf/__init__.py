"""Turn a brand kit and Markdown into consistently branded, multi-page PDFs."""

from importlib.metadata import version

from brandpdf.brand import Brand, BrandError, load_brand, parse_brand
from brandpdf.render import render

__version__ = version("brandpdf")

__all__ = ["Brand", "BrandError", "__version__", "load_brand", "parse_brand", "render"]
