from __future__ import annotations

import pytest

from conftest import FakeClock, FakeWindows
from vortex_autoclicker.config import Config
from vortex_autoclicker.handoff import TabCloser
from vortex_autoclicker.windows import Window, is_browser_title, is_vortex_title

BROWSER = Window(1, "Skyrim Mod - Nexus Mods - Mozilla Firefox")
VORTEX = Window(2, "Vortex")


@pytest.mark.parametrize(
    ("title", "browser", "vortex"),
    [
        ("Some Mod :: Nexus Mods - Google Chrome", True, False),
        ("Vortex", False, True),
        ("Vortex - Nexus Mods", False, False),  # ambiguous: matches neither
        ("Notepad", False, False),
    ],
)
def test_title_predicates(title: str, browser: bool, vortex: bool) -> None:
    assert is_browser_title(title) is browser
    assert is_vortex_title(title) is vortex


def make_closer(windows: FakeWindows, clock: FakeClock, keys: list[tuple[str, ...]]) -> TabCloser:
    return TabCloser(
        Config(handoff_timeout=1.0, close_grace=0.0),
        windows,
        hotkey=lambda *k: keys.append(k),
        sleep=clock.sleep,
        clock=clock,
    )


def test_closes_tab_and_refocuses_vortex(clock: FakeClock) -> None:
    keys: list[tuple[str, ...]] = []
    windows = FakeWindows([BROWSER, VORTEX], foreground=VORTEX.title)

    assert make_closer(windows, clock, keys).close_after_handoff() is True
    assert keys == [("ctrl", "w")]
    assert windows.focused == [BROWSER.handle, VORTEX.handle]


def test_waits_for_timeout_when_vortex_never_takes_focus(clock: FakeClock) -> None:
    windows = FakeWindows([BROWSER, VORTEX], foreground=BROWSER.title)
    closer = make_closer(windows, clock, [])

    assert closer.wait_for_vortex_focus() is False
    assert clock.now >= 1.0


def test_no_browser_window_skips_closing(clock: FakeClock) -> None:
    keys: list[tuple[str, ...]] = []
    windows = FakeWindows([VORTEX], foreground=VORTEX.title)

    assert make_closer(windows, clock, keys).close_nexus_tab() is False
    assert keys == []


def test_focus_failure_skips_closing(clock: FakeClock) -> None:
    keys: list[tuple[str, ...]] = []
    windows = FakeWindows([BROWSER], focus_ok=False)

    assert make_closer(windows, clock, keys).close_nexus_tab() is False
    assert keys == []
