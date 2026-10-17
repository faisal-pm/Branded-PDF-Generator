"""Readable errors for brand kits and documents (F2, F9).

Pydantic's messages are written for Python developers. ``describe`` rewrites them for someone
editing a YAML file: dotted key paths, plain wording, and a suggestion when a key looks like a
typo of a real one.
"""

from __future__ import annotations

import difflib
from typing import Any

from pydantic import BaseModel


class _ProblemsError(Exception):
    kind = ""

    def __init__(self, source: str, problems: list[str]) -> None:
        self.source = source
        self.problems = problems
        header = f"Invalid {self.kind} {source}:" if source else f"Invalid {self.kind}:"
        super().__init__("\n".join([header, *(f"  - {p}" for p in problems)]))


class BrandError(_ProblemsError):
    """A brand kit could not be loaded. ``problems`` lists each issue found."""

    kind = "brand kit"


class DocumentError(_ProblemsError):
    """A document could not be rendered. ``problems`` lists each issue found."""

    kind = "document"

    def __init__(self, problems: list[str], source: str = "") -> None:
        super().__init__(source, problems)


def describe(error: Any, model: type[BaseModel]) -> str:
    """Turn one pydantic error into a line a non-Python user can act on."""
    loc = tuple(str(part) for part in error["loc"])
    kind = error["type"]
    ctx = error.get("ctx", {})

    if kind == "extra_forbidden":
        loc, key = loc[:-1], loc[-1]
        allowed = keys_at(model, loc)
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
        message = (
            f"expected a section of keys ({', '.join(keys_at(model, loc))}), got {error['input']!r}"
        )
    else:
        message = error["msg"]

    return f"{'.'.join(loc)}: {message}" if loc else message


def keys_at(model: type[BaseModel], loc: tuple[str, ...]) -> list[str]:
    """The keys allowed at a location in a model, used to suggest a fix for a typo."""
    for part in loc:
        annotation = model.model_fields[part].annotation if part in model.model_fields else None
        if not (isinstance(annotation, type) and issubclass(annotation, BaseModel)):
            return []
        model = annotation
    return list(model.model_fields)
