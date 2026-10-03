"""Shared pytest fixtures.

The tests never touch the real screen, mouse, keyboard or Win32 API: every
side effect is replaced by the fakes below.
"""

from __future__ import annotations

from collections.abc import Callable

import pytest

from vortex_autoclicker.windows import Window


class FakeClock:
    """Manually advanced monotonic clock; ``sleep`` advances it too."""

    def __init__(self, start: float = 0.0) -> None:
        self.now = start
        self.sleeps: list[float] = []

    def __call__(self) -> float:
        return self.now

    def advance(self, seconds: float) -> None:
        self.now += seconds

    def sleep(self, seconds: float) -> None:
        self.sleeps.append(seconds)
        self.now += seconds


class FakeWindows:
    """In-memory stand-in for :class:`vortex_autoclicker.windows.WindowManager`."""

    def __init__(self, windows: list[Window], foreground: str = "", focus_ok: bool = True) -> None:
        self.windows = windows
        self.foreground = foreground
        self.focus_ok = focus_ok
        self.focused: list[int] = []

    def foreground_title(self) -> str:
        return self.foreground

    def find_windows(self, predicate: Callable[[str], bool]) -> list[Window]:
        return [w for w in self.windows if predicate(w.title)]

    def focus(self, handle: int) -> bool:
        self.focused.append(handle)
        return self.focus_ok


@pytest.fixture
def clock() -> FakeClock:
    return FakeClock()
