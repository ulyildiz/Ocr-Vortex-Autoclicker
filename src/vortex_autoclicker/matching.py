"""Pure text-matching logic: find a button label among OCR results."""

from __future__ import annotations

from collections.abc import Iterable
from difflib import SequenceMatcher
from typing import NamedTuple

DEFAULT_MATCH_THRESHOLD = 0.9


class TextItem(NamedTuple):
    """A piece of text recognised on screen, with the centre of its bounding box."""

    text: str
    x: float
    y: float


class Point(NamedTuple):
    """A screen coordinate in pixels."""

    x: float
    y: float


def normalize(text: str) -> str:
    """Normalise text for comparison: trim, lower-case, drop trailing dots."""
    return text.strip().lower().rstrip(".")


def similarity(a: str, b: str) -> float:
    """Return the similarity ratio (0-1) of two strings after normalisation."""
    return SequenceMatcher(None, normalize(a), normalize(b)).ratio()


def find_button(
    items: Iterable[TextItem],
    label: str,
    threshold: float = DEFAULT_MATCH_THRESHOLD,
) -> Point | None:
    """Locate a button label among OCR results.

    Args:
        items: Text recognised on screen.
        label: The button label to look for.
        threshold: Minimum similarity ratio required for a match.

    Returns:
        The centre of the top-most matching text, or ``None`` if nothing matches.
    """
    matches = [Point(item.x, item.y) for item in items if similarity(item.text, label) >= threshold]
    if not matches:
        return None
    return min(matches, key=lambda point: point.y)
