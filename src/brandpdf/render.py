"""Public rendering API (F13)."""

from __future__ import annotations

from typing import Any


def render(markdown: str, brand: Any) -> bytes:
    """Render Markdown with a brand kit and return the PDF as bytes."""
    raise NotImplementedError("render() is not implemented yet")
