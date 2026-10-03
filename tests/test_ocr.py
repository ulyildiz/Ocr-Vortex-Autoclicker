from __future__ import annotations

from types import SimpleNamespace

import pytest

from vortex_autoclicker.exceptions import OcrError
from vortex_autoclicker.matching import TextItem
from vortex_autoclicker.ocr import ScreenReader, box_center, parse_ocr_output

SQUARE = [[0, 0], [10, 0], [10, 20], [0, 20]]


def test_box_center() -> None:
    assert box_center(SQUARE) == (5.0, 10.0)


def test_box_center_empty_raises() -> None:
    with pytest.raises(OcrError):
        box_center([])


def test_parse_new_api_output() -> None:
    output = SimpleNamespace(boxes=[SQUARE], txts=("Install",))
    assert parse_ocr_output(output) == [TextItem("Install", 5.0, 10.0)]


def test_parse_new_api_output_with_nothing_found() -> None:
    assert parse_ocr_output(SimpleNamespace(boxes=None, txts=None)) == []


def test_parse_legacy_api_output() -> None:
    output = ([(SQUARE, "Slow download", 0.98)], [0.1, 0.2, 0.3])
    assert parse_ocr_output(output) == [TextItem("Slow download", 5.0, 10.0)]


def test_parse_legacy_api_output_with_nothing_found() -> None:
    assert parse_ocr_output((None, None)) == []


def test_parse_garbage_raises_ocr_error() -> None:
    with pytest.raises(OcrError):
        parse_ocr_output(42)


def test_screen_reader_uses_injected_engine_and_grabber() -> None:
    image = object()
    seen: list[object] = []

    def engine(img: object) -> SimpleNamespace:
        seen.append(img)
        return SimpleNamespace(boxes=[SQUARE], txts=["Install"])

    reader = ScreenReader(engine=engine, grab=lambda: image)
    assert reader() == [TextItem("Install", 5.0, 10.0)]
    assert seen == [image]
