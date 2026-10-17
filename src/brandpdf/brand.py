"""Brand kit model and YAML loader (F1, F2).

A brand kit is a YAML file that every document inherits: name, colour palette, fonts, logo,
contact block, page setup and optional letterhead backgrounds. Relative paths in the kit are
resolved against the folder that holds the kit file, so a kit and its assets can move together.
"""

from __future__ import annotations

import difflib
import re
from collections.abc import Mapping
from importlib.resources import files
from pathlib import Path
from typing import Annotated, Any, Literal

import yaml
from PIL import Image, UnidentifiedImageError
from pydantic import (
    BaseModel,
    BeforeValidator,
    ConfigDict,
    Field,
    ValidationError,
    ValidationInfo,
    field_validator,
    model_validator,
)
from pypdf import PdfReader
from pypdf.errors import PyPdfError
from reportlab.lib.pagesizes import A4, A5, LEGAL, LETTER
from reportlab.lib.units import mm
from reportlab.pdfbase.ttfonts import TTFError, TTFont

BUILTIN_FONTS = (
    "Helvetica",
    "Helvetica-Bold",
    "Helvetica-Oblique",
    "Helvetica-BoldOblique",
    "Times-Roman",
    "Times-Bold",
    "Times-Italic",
    "Times-BoldItalic",
    "Courier",
    "Courier-Bold",
    "Courier-Oblique",
    "Courier-BoldOblique",
)

PAGE_SIZES = {"A4": A4, "A5": A5, "Letter": LETTER, "Legal": LEGAL}

IMAGE_SUFFIXES = (".png", ".jpg", ".jpeg")
LETTERHEAD_SUFFIXES = (".pdf", *IMAGE_SUFFIXES)

_HEX_RE = re.compile(r"#(?:[0-9a-fA-F]{3}|[0-9a-fA-F]{6})")


class BrandError(Exception):
    """A brand kit could not be loaded. ``problems`` lists each issue found."""

    def __init__(self, source: str, problems: list[str]) -> None:
        self.source = source
        self.problems = problems
        header = f"Invalid brand kit {source}:" if source else "Invalid brand kit:"
        super().__init__("\n".join([header, *(f"  - {p}" for p in problems)]))


def _hex_colour(value: Any) -> str:
    if value is None:
        raise ValueError(
            "value is empty; in YAML a bare # starts a comment, "
            'so quote hex colours, e.g. "#1F4E79"'
        )
    if not isinstance(value, str) or not _HEX_RE.fullmatch(value):
        raise ValueError(f'{value!r} is not a hex colour (expected "#RRGGBB" or "#RGB")')
    digits = value[1:].upper()
    if len(digits) == 3:
        digits = "".join(d * 2 for d in digits)
    return f"#{digits}"


HexColour = Annotated[str, BeforeValidator(_hex_colour)]


def _resolve_file(value: Any, info: ValidationInfo, suffixes: tuple[str, ...]) -> Path:
    """Resolve a path from the kit against its folder and check it is an existing file."""
    if not isinstance(value, (str, Path)):
        raise ValueError(f"expected a file path, got {value!r}")
    path = Path(value).expanduser()
    if path.suffix.lower() not in suffixes:
        *rest, last = suffixes
        allowed = f"{', '.join(rest)} or {last}" if rest else last
        raise ValueError(f"'{value}' must be a {allowed} file")
    base_dir = (info.context or {}).get("base_dir", Path.cwd())
    path = (Path(base_dir) / path).resolve()
    if not path.is_file():
        raise ValueError(f"file not found: {path}")
    if path.suffix.lower() == ".pdf":
        _check_pdf(path)
    elif path.suffix.lower() in IMAGE_SUFFIXES:
        _check_image(path)
    return path


def _check_pdf(path: Path) -> None:
    try:
        pages = len(PdfReader(path).pages)
    except (PyPdfError, OSError, ValueError, KeyError):
        pages = 0
    if pages == 0:
        raise ValueError(f"{path} is not a readable PDF")


def _check_image(path: Path) -> None:
    try:
        with Image.open(path) as image:
            image.verify()
    except (UnidentifiedImageError, OSError, SyntaxError):
        raise ValueError(f"{path} is not a readable PNG or JPEG image") from None


class _Model(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, coerce_numbers_to_str=True)


class Colors(_Model):
    primary: HexColour
    secondary: HexColour
    accent: HexColour
    text: HexColour = "#1A1A1A"
    background: HexColour = "#FFFFFF"


class Fonts(_Model):
    """Each font is a built-in PDF font name (str) or a resolved path to a TrueType file."""

    heading: str | Path = "Helvetica-Bold"
    body: str | Path = "Helvetica"

    @field_validator("heading", "body", mode="before")
    @classmethod
    def _font(cls, value: Any, info: ValidationInfo) -> str | Path:
        if value in BUILTIN_FONTS:
            return value
        if not isinstance(value, (str, Path)) or Path(value).suffix.lower() != ".ttf":
            raise ValueError(
                f"{str(value)!r} is not a built-in font or a .ttf file "
                f"(built-in fonts: {', '.join(BUILTIN_FONTS)})"
            )
        path = _resolve_file(value, info, (".ttf",))
        try:
            TTFont(f"brandpdf-probe-{path.stem}", str(path))
        except (TTFError, OSError) as exc:
            raise ValueError(f"{path} is not a valid TrueType font ({exc})") from None
        return path


class Contact(_Model):
    address: str | None = None
    phone: str | None = None
    email: str | None = None
    website: str | None = None


class Margins(_Model):
    """Page margins in millimetres."""

    top: float = Field(20, ge=0)
    right: float = Field(20, ge=0)
    bottom: float = Field(20, ge=0)
    left: float = Field(20, ge=0)


class Page(_Model):
    size: Literal["A4", "A5", "Letter", "Legal"] = "A4"
    margins_mm: Margins = Margins()

    @property
    def dimensions(self) -> tuple[float, float]:
        """Page width and height in PDF points."""
        return PAGE_SIZES[self.size]

    @model_validator(mode="after")
    def _margins_fit(self) -> Page:
        width, height = (side / mm for side in self.dimensions)
        m = self.margins_mm
        if m.left + m.right >= width:
            raise ValueError(
                f"left and right margins ({m.left + m.right:g} mm) leave no room "
                f"on {self.size} ({width:.0f} mm wide)"
            )
        if m.top + m.bottom >= height:
            raise ValueError(
                f"top and bottom margins ({m.top + m.bottom:g} mm) leave no room "
                f"on {self.size} ({height:.0f} mm tall)"
            )
        return self


class Letterhead(_Model):
    """Background files drawn behind the first page and the pages after it."""

    first_page: Path | None = None
    continuation: Path | None = None

    @field_validator("first_page", "continuation", mode="before")
    @classmethod
    def _background(cls, value: Any, info: ValidationInfo) -> Path | None:
        return None if value is None else _resolve_file(value, info, LETTERHEAD_SUFFIXES)


class Brand(_Model):
    name: str = Field(min_length=1)
    colors: Colors
    fonts: Fonts = Fonts()
    logo: Path | None = None
    contact: Contact = Contact()
    page: Page = Page()
    letterhead: Letterhead = Letterhead()

    @field_validator("logo", mode="before")
    @classmethod
    def _logo(cls, value: Any, info: ValidationInfo) -> Path | None:
        return None if value is None else _resolve_file(value, info, IMAGE_SUFFIXES)


def parse_brand(data: Mapping[str, Any], base_dir: str | Path = ".", source: str = "") -> Brand:
    """Validate a brand kit mapping. Relative paths resolve against ``base_dir``."""
    try:
        return Brand.model_validate(data, context={"base_dir": Path(base_dir)})
    except ValidationError as exc:
        raise BrandError(source, [_describe(error) for error in exc.errors()]) from None


def load_brand(path: str | Path) -> Brand:
    """Load and validate a brand kit YAML file."""
    path = Path(path)
    try:
        text = path.read_text(encoding="utf-8")
    except FileNotFoundError:
        raise BrandError(str(path), [f"Brand kit not found: {path}"]) from None
    except OSError as exc:
        raise BrandError(str(path), [f"cannot read the file ({exc.strerror})"]) from None

    try:
        data = yaml.safe_load(text)
    except yaml.YAMLError as exc:
        mark = getattr(exc, "problem_mark", None)
        where = f" at line {mark.line + 1}, column {mark.column + 1}" if mark else ""
        problem = getattr(exc, "problem", None) or "could not be parsed"
        raise BrandError(str(path), [f"the file is not valid YAML{where}: {problem}"]) from None

    if not isinstance(data, Mapping):
        raise BrandError(str(path), ["expected keys such as 'name' and 'colors' at the top level"])
    return parse_brand(data, base_dir=path.parent, source=str(path))


def starter_kit() -> str:
    """The commented brand kit that ``brandpdf init`` writes."""
    return files("brandpdf").joinpath("starter_brand.yaml").read_text(encoding="utf-8")


def _describe(error: Any) -> str:
    """Turn one pydantic error into a line a non-Python user can act on."""
    loc = tuple(str(part) for part in error["loc"])
    kind = error["type"]
    ctx = error.get("ctx", {})

    if kind == "extra_forbidden":
        loc, key = loc[:-1], loc[-1]
        allowed = _keys_at(loc)
        match = difflib.get_close_matches(key, allowed, n=1)
        hint = f"did you mean '{match[0]}'?" if match else f"allowed: {', '.join(allowed)}"
        message = f"unknown key '{key}' ({hint})"
    elif kind == "missing":
        message = "required key missing"
    elif kind == "value_error":
        message = str(ctx["error"])
    elif kind == "literal_error":
        message = f"{error['input']!r} is not one of {ctx['expected']}"
    elif kind == "greater_than_equal":
        message = f"must be at least {ctx['ge']:g} (got {error['input']:g})"
    elif kind == "string_too_short":
        message = "must not be empty"
    elif kind in ("float_parsing", "float_type"):
        message = f"expected a number, got {error['input']!r}"
    elif kind == "string_type":
        message = f"expected text, got {error['input']!r}"
    elif kind == "model_type":
        message = f"expected a section of keys ({', '.join(_keys_at(loc))}), got {error['input']!r}"
    else:
        message = error["msg"]

    return f"{'.'.join(loc)}: {message}" if loc else message


def _keys_at(loc: tuple[str, ...]) -> list[str]:
    """The keys allowed at a location in the kit, used to suggest a fix for a typo."""
    model: type[BaseModel] = Brand
    for part in loc:
        annotation = model.model_fields[part].annotation if part in model.model_fields else None
        if not (isinstance(annotation, type) and issubclass(annotation, BaseModel)):
            return []
        model = annotation
    return list(model.model_fields)
