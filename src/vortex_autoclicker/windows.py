"""Win32 window discovery and focus handling (Windows only)."""

from __future__ import annotations

import logging
import time
from collections.abc import Callable
from typing import Any, NamedTuple, Protocol

from vortex_autoclicker.exceptions import UnsupportedPlatformError
from vortex_autoclicker.utils import is_windows, require_module

logger = logging.getLogger(__name__)

SW_RESTORE = 9
#: Seconds to wait after ``SetForegroundWindow`` before checking the result.
FOCUS_SETTLE_DELAY = 0.3


class Window(NamedTuple):
    """A top-level window: its native handle and its title."""

    handle: int
    title: str


TitlePredicate = Callable[[str], bool]


class WindowBackend(Protocol):
    """The window operations the tab-closing logic depends on."""

    def foreground_title(self) -> str:
        """Return the title of the currently focused window."""
        ...

    def find_windows(self, predicate: TitlePredicate) -> list[Window]:
        """Return visible top-level windows whose title passes ``predicate``."""
        ...

    def focus(self, handle: int) -> bool:
        """Bring a window to the front; return ``True`` if it got focus."""
        ...


def title_matches(title: str, include: str, exclude: str) -> bool:
    """Return ``True`` if ``title`` contains ``include`` but not ``exclude``.

    The comparison is case-insensitive.
    """
    low = title.lower()
    return include.lower() in low and exclude.lower() not in low


def is_browser_title(
    title: str, browser_keyword: str = "nexus", vortex_keyword: str = "vortex"
) -> bool:
    """Return ``True`` if ``title`` looks like the browser window showing Nexus Mods."""
    return title_matches(title, browser_keyword, vortex_keyword)


def is_vortex_title(
    title: str, vortex_keyword: str = "vortex", browser_keyword: str = "nexus"
) -> bool:
    """Return ``True`` if ``title`` looks like the Vortex mod manager window."""
    return title_matches(title, vortex_keyword, browser_keyword)


class WindowManager:
    """Thin wrapper around the ``user32`` Win32 API.

    Raises:
        UnsupportedPlatformError: When instantiated on a non-Windows system.
    """

    def __init__(self) -> None:
        if not is_windows():
            raise UnsupportedPlatformError("Window management is only supported on Windows.")
        import ctypes
        from ctypes import wintypes

        # Typed as Any: ``windll``/``WINFUNCTYPE`` only exist in the Windows stubs.
        self._ctypes: Any = ctypes
        self._wintypes = wintypes
        self._user32: Any = self._ctypes.windll.user32
        self._configure_signatures()

    def _configure_signatures(self) -> None:
        """Declare argument/return types so handles are marshalled correctly."""
        u32, wt, ct = self._user32, self._wintypes, self._ctypes
        u32.GetWindowTextLengthW.argtypes = [wt.HWND]
        u32.GetWindowTextW.argtypes = [wt.HWND, wt.LPWSTR, ct.c_int]
        u32.IsWindowVisible.argtypes = [wt.HWND]
        u32.IsIconic.argtypes = [wt.HWND]
        u32.ShowWindow.argtypes = [wt.HWND, ct.c_int]
        u32.SetForegroundWindow.argtypes = [wt.HWND]
        u32.GetForegroundWindow.restype = wt.HWND

    def window_title(self, handle: int | None) -> str:
        """Return the title of a window, or ``""`` for a null handle."""
        if not handle:
            return ""
        length = self._user32.GetWindowTextLengthW(handle)
        buffer = self._ctypes.create_unicode_buffer(length + 1)
        self._user32.GetWindowTextW(handle, buffer, length + 1)
        return str(buffer.value)

    def foreground_window(self) -> int:
        """Return the handle of the focused window (``0`` if none)."""
        return int(self._user32.GetForegroundWindow() or 0)

    def foreground_title(self) -> str:
        """Return the title of the focused window."""
        return self.window_title(self.foreground_window())

    def find_windows(self, predicate: TitlePredicate) -> list[Window]:
        """Return visible top-level windows whose title passes ``predicate``.

        Windows are returned in Z-order, i.e. top-most first.
        """
        found: list[Window] = []
        wt = self._wintypes
        enum_proc = self._ctypes.WINFUNCTYPE(wt.BOOL, wt.HWND, wt.LPARAM)

        def collect(handle: int, _lparam: int) -> bool:
            if self._user32.IsWindowVisible(handle):
                title = self.window_title(handle)
                if predicate(title):
                    found.append(Window(int(handle), title))
            return True

        self._user32.EnumWindows(enum_proc(collect), 0)
        return found

    def focus(self, handle: int, settle_delay: float = FOCUS_SETTLE_DELAY) -> bool:
        """Bring a window to the front.

        Windows only lets the foreground process change focus; tapping ``Alt``
        first is a well-known workaround that makes ``SetForegroundWindow``
        succeed.

        Returns:
            ``True`` if the window really received focus.
        """
        if self._user32.IsIconic(handle):
            self._user32.ShowWindow(handle, SW_RESTORE)
        keyboard = require_module("keyboard")
        keyboard.press_and_release("alt")
        self._user32.SetForegroundWindow(handle)
        time.sleep(settle_delay)
        return self.foreground_window() == handle
