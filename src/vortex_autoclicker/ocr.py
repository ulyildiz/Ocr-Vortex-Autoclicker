"""Screen capture and OCR (via RapidOCR)."""

from __future__ import annotations

import logging
from collections.abc import Callable, Iterable, Sequence
from typing import Any

from vortex_autoclicker.exceptions import DependencyError, OcrError
from vortex_autoclicker.matching import TextItem
from vortex_autoclicker.utils import require_module

logger = logging.getLogger(__name__)

#: Callable that runs OCR on an image and returns the raw engine output.
OcrEngine = Callable[[Any], Any]
#: Callable that captures the screen and returns a BGR image array.
ScreenGrabber = Callable[[], Any]


def load_rapidocr() -> OcrEngine:
    """Instantiate RapidOCR, supporting both the new and the legacy package.

    Raises:
        DependencyError: If neither ``rapidocr`` nor ``rapidocr_onnxruntime``
            is installed.
    """
    try:
        from rapidocr import RapidOCR  # newer package
    except ImportError:
        try:
            from rapidocr_onnxruntime import RapidOCR  # older package
        except ImportError as exc:
            raise DependencyError(
                "No OCR backend found. Install it with: pip install rapidocr onnxruntime"
            ) from exc
    engine: OcrEngine = RapidOCR()
    return engine


def grab_screen_bgr() -> Any:
    """Capture the primary screen as a BGR ``numpy`` array (OpenCV layout)."""
    pyautogui = require_module("pyautogui")
    cv2 = require_module("cv2", "opencv-python")
    np = require_module("numpy")
    return cv2.cvtColor(np.array(pyautogui.screenshot()), cv2.COLOR_RGB2BGR)


def box_center(box: Iterable[Sequence[float]]) -> tuple[float, float]:
    """Return the centre of a polygon given as ``[(x, y), ...]`` points."""
    points = [(float(point[0]), float(point[1])) for point in box]
    if not points:
        raise OcrError("Bounding box has no points.")
    count = len(points)
    return sum(x for x, _ in points) / count, sum(y for _, y in points) / count


def parse_ocr_output(output: Any) -> list[TextItem]:
    """Convert raw RapidOCR output into :class:`TextItem` objects.

    Two output formats are supported:

    * **New API** (``rapidocr``): an object with ``boxes`` and ``txts``
      attributes, either of which may be ``None`` when nothing was found.
    * **Legacy API** (``rapidocr_onnxruntime``): a ``(result, elapse)`` tuple
      where ``result`` is ``None`` or a list of ``(box, text, score)``.

    Raises:
        OcrError: If the output has an unexpected shape.
    """
    try:
        if hasattr(output, "txts"):
            boxes = output.boxes if output.boxes is not None else []
            texts = output.txts if output.txts is not None else []
        else:
            result = output[0] or []
            boxes = [entry[0] for entry in result]
            texts = [entry[1] for entry in result]
        pairs = zip(boxes, texts, strict=False)
        return [TextItem(str(text), *box_center(box)) for box, text in pairs]
    except (TypeError, IndexError, KeyError, ValueError) as exc:
        raise OcrError(f"Unexpected OCR output format: {exc}") from exc


class ScreenReader:
    """Capture the screen and extract on-screen text with OCR.

    Instances are callable, so they can be passed directly as the
    ``read_screen`` dependency of :class:`~vortex_autoclicker.clicker.AutoClicker`.

    Args:
        engine: OCR engine to use. Defaults to a lazily created RapidOCR instance.
        grab: Screen-capture function. Defaults to :func:`grab_screen_bgr`.
    """

    def __init__(self, engine: OcrEngine | None = None, grab: ScreenGrabber | None = None) -> None:
        self._engine = engine
        self._grab = grab or grab_screen_bgr

    @property
    def engine(self) -> OcrEngine:
        """The OCR engine, created on first access."""
        if self._engine is None:
            self._engine = load_rapidocr()
        return self._engine

    def read_image(self, image: Any) -> list[TextItem]:
        """Run OCR on an already captured image."""
        return parse_ocr_output(self.engine(image))

    def read_screen(self) -> list[TextItem]:
        """Capture the primary screen and run OCR on it."""
        items = self.read_image(self._grab())
        logger.debug("OCR found %d text items", len(items))
        return items

    def warm_up(self) -> None:
        """Load the OCR models up front so the first real scan is fast."""
        self.read_screen()

    def __call__(self) -> list[TextItem]:
        return self.read_screen()
