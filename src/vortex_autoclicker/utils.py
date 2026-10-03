"""Small, dependency-free helper functions."""

from __future__ import annotations

import importlib
import sys
from types import ModuleType

from vortex_autoclicker.exceptions import DependencyError


def is_windows() -> bool:
    """Return ``True`` when running on Microsoft Windows."""
    return sys.platform == "win32"


def require_module(name: str, pip_name: str | None = None) -> ModuleType:
    """Import a module lazily, turning a missing package into a friendly error.

    Args:
        name: The importable module name (e.g. ``"cv2"``).
        pip_name: The distribution name to suggest for installation when it
            differs from ``name`` (e.g. ``"opencv-python"``).

    Returns:
        The imported module object.

    Raises:
        DependencyError: If the module cannot be imported.
    """
    try:
        return importlib.import_module(name)
    except ImportError as exc:
        raise DependencyError(
            f"Required module '{name}' is not installed. "
            f"Install it with: pip install {pip_name or name}"
        ) from exc
