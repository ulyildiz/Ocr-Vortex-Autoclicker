from __future__ import annotations

import pytest

from vortex_autoclicker.matching import Point, TextItem, find_button, normalize, similarity


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("  Slow download  ", "slow download"),
        ("Install...", "install"),
        ("DOWNLOAD MANUALLY.", "download manually"),
        ("", ""),
    ],
)
def test_normalize(raw: str, expected: str) -> None:
    assert normalize(raw) == expected


def test_similarity_is_case_and_punctuation_insensitive() -> None:
    assert similarity("Slow Download.", "slow download") == 1.0


def test_find_button_returns_center_of_match() -> None:
    items = [TextItem("Fast download", 10, 10), TextItem("Slow download", 100, 200)]
    assert find_button(items, "Slow download") == Point(100, 200)


def test_find_button_tolerates_small_ocr_errors() -> None:
    items = [TextItem("Slow downl0ad", 5, 5)]
    assert find_button(items, "Slow download", threshold=0.9) == Point(5, 5)


def test_find_button_rejects_below_threshold() -> None:
    items = [TextItem("Install", 1, 1)]
    assert find_button(items, "Uninstall", threshold=0.95) is None


def test_find_button_prefers_top_most_match() -> None:
    items = [TextItem("Install", x, y) for x, y in [(50, 300), (60, 120), (70, 900)]]
    assert find_button(items, "Install") == Point(60, 120)


def test_find_button_with_no_items() -> None:
    assert find_button([], "Install") is None
