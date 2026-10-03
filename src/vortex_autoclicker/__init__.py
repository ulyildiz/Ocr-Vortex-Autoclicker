"""Vortex Auto-Clicker: OCR-driven automation for Vortex + Nexus Mods downloads.

The package can be used both as a command-line tool (``vortex-autoclicker`` or
``python -m vortex_autoclicker``) and as an importable library::

    from vortex_autoclicker import Config, run

    run(Config(close_page=False))

Importing the package is cheap: heavy third-party dependencies (OCR engine,
PyAutoGUI, keyboard hooks, Win32 API) are only loaded when they are actually
needed.
"""

from __future__ import annotations

import logging

from vortex_autoclicker.clicker import AutoClicker, build_default_clicker, run
from vortex_autoclicker.config import DEFAULT_STEPS, Config, Step
from vortex_autoclicker.exceptions import (
    ConfigError,
    DependencyError,
    OcrError,
    UnsupportedPlatformError,
    VortexAutoClickerError,
)
from vortex_autoclicker.handoff import TabCloser
from vortex_autoclicker.matching import Point, TextItem, find_button, normalize
from vortex_autoclicker.ocr import ScreenReader, parse_ocr_output

__version__ = "0.1.0"

__all__ = [
    "DEFAULT_STEPS",
    "AutoClicker",
    "Config",
    "ConfigError",
    "DependencyError",
    "OcrError",
    "Point",
    "ScreenReader",
    "Step",
    "TabCloser",
    "TextItem",
    "UnsupportedPlatformError",
    "VortexAutoClickerError",
    "__version__",
    "build_default_clicker",
    "find_button",
    "normalize",
    "parse_ocr_output",
    "run",
]

# Library best practice: never emit log output unless the application opts in.
logging.getLogger(__name__).addHandler(logging.NullHandler())
