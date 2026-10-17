from __future__ import annotations

import importlib
from types import SimpleNamespace

import pytest

from vortex_autoclicker.exceptions import DependencyError, OcrError
from vortex_autoclicker.matching import TextItem
from vortex_autoclicker.ocr import ScreenReader, box_center, load_rapidocr, parse_ocr_output

SQUARE = [[0, 0], [10, 0], [10, 20], [0, 20]]


def fake_import(available: dict[str, object]):  # type: ignore[no-untyped-def]
    def import_module(name: str) -> object:
        if name not in available:
            raise ImportError(name)
        return available[name]

    return import_module


@pytest.mark.parametrize(
    ("installed", "expected"),
    [
        (["rapidocr", "rapidocr_onnxruntime"], "new"),
        (["rapidocr_onnxruntime"], "legacy"),
    ],
)
def test_load_rapidocr_prefers_new_package(
    monkeypatch: pytest.MonkeyPatch, installed: list[str], expected: str
) -> None:
    modules = {
        "rapidocr": SimpleNamespace(RapidOCR=lambda: "new"),
        "rapidocr_onnxruntime": SimpleNamespace(RapidOCR=lambda: "legacy"),
    }
    available = {name: modules[name] for name in installed}
    monkeypatch.setattr(importlib, "import_module", fake_import(available))
    assert load_rapidocr() == expected


def test_load_rapidocr_without_backend_raises(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(importlib, "import_module", fake_import({}))
    with pytest.raises(DependencyError):
        load_rapidocr()


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
