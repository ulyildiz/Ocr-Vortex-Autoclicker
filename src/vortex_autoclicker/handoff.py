"""Close the Nexus Mods browser tab once a download was handed over to Vortex.

The logic does not need to *see* the tab: it finds the browser window by its
title, focuses it, presses ``Ctrl+W`` (closing only the active tab, never the
whole browser) and finally brings Vortex back to the front so the next popup
is visible to OCR.
"""

from __future__ import annotations

import logging
import time
from collections.abc import Callable

from vortex_autoclicker.config import Config
from vortex_autoclicker.utils import require_module
from vortex_autoclicker.windows import WindowBackend, is_browser_title, is_vortex_title

logger = logging.getLogger(__name__)

#: Pause between closing the tab and re-focusing Vortex.
REFOCUS_DELAY = 0.4
#: Polling interval while waiting for Vortex to take focus.
FOCUS_POLL_INTERVAL = 0.1

Hotkey = Callable[..., None]


def pyautogui_hotkey(*keys: str) -> None:
    """Press a key combination using PyAutoGUI."""
    require_module("pyautogui").hotkey(*keys)


class TabCloser:
    """Callable that performs the post-download "close the Nexus tab" routine.

    Args:
        config: Settings (keywords, timeouts).
        windows: Window backend, usually a
            :class:`~vortex_autoclicker.windows.WindowManager`.
        hotkey: Function used to press ``Ctrl+W``.
        sleep: Sleep function (injectable for tests).
        clock: Monotonic clock (injectable for tests).
    """

    def __init__(
        self,
        config: Config,
        windows: WindowBackend,
        *,
        hotkey: Hotkey = pyautogui_hotkey,
        sleep: Callable[[float], None] = time.sleep,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        self._config = config
        self._windows = windows
        self._hotkey = hotkey
        self._sleep = sleep
        self._clock = clock

    def is_browser_title(self, title: str) -> bool:
        """Return ``True`` if ``title`` belongs to the Nexus browser window."""
        cfg = self._config
        return is_browser_title(title, cfg.browser_title_keyword, cfg.vortex_title_keyword)

    def is_vortex_title(self, title: str) -> bool:
        """Return ``True`` if ``title`` belongs to the Vortex window."""
        cfg = self._config
        return is_vortex_title(title, cfg.vortex_title_keyword, cfg.browser_title_keyword)

    def wait_for_vortex_focus(self) -> bool:
        """Wait until Vortex grabs focus, which happens once it receives the nxm link.

        Returns:
            ``True`` if Vortex took focus before ``config.handoff_timeout``.
        """
        deadline = self._clock() + self._config.handoff_timeout
        while self._clock() < deadline:
            if self.is_vortex_title(self._windows.foreground_title()):
                return True
            self._sleep(FOCUS_POLL_INTERVAL)
        return False

    def close_nexus_tab(self) -> bool:
        """Focus the browser window showing Nexus Mods and close its active tab.

        Returns:
            ``True`` if ``Ctrl+W`` was sent to the browser.
        """
        windows = self._windows.find_windows(self.is_browser_title)
        if not windows:
            open_titles = [w.title for w in self._windows.find_windows(lambda t: bool(t.strip()))]
            logger.warning(
                "Close page: no window with %r in its title. Open windows:\n    %s",
                self._config.browser_title_keyword,
                "\n    ".join(open_titles) or "(none)",
            )
            return False

        target = windows[0]
        if not self._windows.focus(target.handle):
            logger.warning("Close page: could not bring the browser to the front, skipped")
            return False

        self._hotkey("ctrl", "w")
        logger.info("Closed tab: %s", target.title)
        return True

    def close_after_handoff(self) -> bool:
        """Wait for the download hand-over, close the Nexus tab and restore Vortex.

        Returns:
            ``True`` if the tab was closed.
        """
        if not self.wait_for_vortex_focus():
            logger.warning(
                "Vortex did not take focus within %ss, closing anyway",
                self._config.handoff_timeout,
            )
        self._sleep(self._config.close_grace)

        vortex_windows = self._windows.find_windows(self.is_vortex_title)
        closed = self.close_nexus_tab()
        self._sleep(REFOCUS_DELAY)
        if vortex_windows:
            # Bring Vortex back so OCR can see the next popup.
            self._windows.focus(vortex_windows[0].handle)
        return closed

    def __call__(self) -> None:
        self.close_after_handoff()
