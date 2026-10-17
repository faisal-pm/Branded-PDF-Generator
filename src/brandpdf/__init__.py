"""Turn a brand kit and Markdown into consistently branded, multi-page PDFs."""

from importlib.metadata import version

from brandpdf.brand import Brand, load_brand, parse_brand
from brandpdf.errors import BrandError, DocumentError
from brandpdf.render import render

__version__ = version("brandpdf")

__all__ = [
    "Brand",
    "BrandError",
    "DocumentError",
    "__version__",
    "load_brand",
    "parse_brand",
    "render",
]
