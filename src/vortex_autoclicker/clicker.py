"""The main scan-and-click loop."""

from __future__ import annotations

import logging
import time
from collections.abc import Callable, Sequence

from vortex_autoclicker.config import Config, Step
from vortex_autoclicker.matching import TextItem, find_button, normalize
from vortex_autoclicker.utils import is_windows, require_module

logger = logging.getLogger(__name__)

#: Returns the text currently visible on screen.
ReadScreen = Callable[[], Sequence[TextItem]]
#: Clicks at the given screen coordinate.
ClickFn = Callable[[float, float], None]
#: Returns ``True`` when the loop should stop.
StopCondition = Callable[[], bool]


class AutoClicker:
    """Repeatedly scans the screen and clicks the highest-priority visible button.

    All side effects are injected, which keeps the class platform-independent
    and easy to test. Use :func:`build_default_clicker` for the real thing.

    Args:
        config: Settings (steps, threshold, poll interval, ...).
        read_screen: Returns the text items currently on screen.
        click: Performs a mouse click at ``(x, y)``.
        should_stop: Checked before every scan; ``True`` ends :meth:`run`.
        after_trigger_click: Called after ``config.close_trigger_label`` was
            clicked (e.g. a :class:`~vortex_autoclicker.handoff.TabCloser`).
        clock: Monotonic clock used for cooldowns.
        sleep: Sleep function used between scans.
    """

    def __init__(
        self,
        config: Config,
        *,
        read_screen: ReadScreen,
        click: ClickFn,
        should_stop: StopCondition,
        after_trigger_click: Callable[[], object] | None = None,
        clock: Callable[[], float] = time.monotonic,
        sleep: Callable[[float], None] = time.sleep,
    ) -> None:
        self._config = config
        self._read_screen = read_screen
        self._click = click
        self._should_stop = should_stop
        self._after_trigger_click = after_trigger_click
        self._clock = clock
        self._sleep = sleep
        self._last_click: dict[str, float] = {}

    @property
    def config(self) -> Config:
        """The active configuration."""
        return self._config

    def is_on_cooldown(self, step: Step, now: float) -> bool:
        """Return ``True`` if ``step`` was clicked less than ``step.cooldown`` ago."""
        last = self._last_click.get(step.label)
        return last is not None and now - last < step.cooldown

    def _is_trigger(self, step: Step) -> bool:
        return normalize(step.label) == normalize(self._config.close_trigger_label)

    def scan_once(self) -> str | None:
        """Scan the screen once and click at most one button.

        Steps are tried in priority order; after a click the scan ends because
        the screen has most likely changed.

        Returns:
            The label that was clicked, or ``None`` if nothing was clicked.
        """
        items = self._read_screen()
        now = self._clock()

        for step in self._config.steps:
            if self.is_on_cooldown(step, now):
                continue
            hit = find_button(items, step.label, self._config.match_threshold)
            if hit is None:
                continue

            self._click(hit.x, hit.y)
            self._last_click[step.label] = self._clock()
            logger.info("Clicked: %s", step.label)

            if self._after_trigger_click is not None and self._is_trigger(step):
                self._after_trigger_click()
                # Restart the cooldown: the hand-over may have taken a while.
                self._last_click[step.label] = self._clock()
            return step.label
        return None

    def run(self) -> None:
        """Scan and click until ``should_stop`` returns ``True``."""
        logger.info("=== Vortex Auto-Clicker (OCR) started ===")
        logger.info("Press [%s] to stop.", self._config.stop_key.upper())
        while not self._should_stop():
            self.scan_once()
            self._sleep(self._config.poll_interval)
        logger.info("Stopped.")


def build_default_clicker(config: Config | None = None, *, warm_up: bool = True) -> AutoClicker:
    """Create an :class:`AutoClicker` wired to the real screen, mouse and keyboard.

    Args:
        config: Settings; defaults to :class:`~vortex_autoclicker.config.Config`.
        warm_up: Load the OCR models before returning.

    Raises:
        DependencyError: If a required third-party package is missing.
    """
    # Local imports keep ``import vortex_autoclicker`` free of heavy dependencies.
    from vortex_autoclicker.handoff import TabCloser
    from vortex_autoclicker.ocr import ScreenReader
    from vortex_autoclicker.windows import WindowManager

    config = config or Config()
    pyautogui = require_module("pyautogui")
    keyboard = require_module("keyboard")

    after_trigger: Callable[[], object] | None = None
    if config.close_page:
        if is_windows():
            after_trigger = TabCloser(config, WindowManager())
        else:
            logger.warning("Closing the page is only supported on Windows, disabling it.")

    reader = ScreenReader()
    if warm_up:
        logger.info("Loading OCR engine...")
        reader.warm_up()

    def click(x: float, y: float) -> None:
        pyautogui.click(x, y)

    def should_stop() -> bool:
        return bool(keyboard.is_pressed(config.stop_key))

    return AutoClicker(
        config,
        read_screen=reader,
        click=click,
        should_stop=should_stop,
        after_trigger_click=after_trigger,
    )


def run(config: Config | None = None) -> None:
    """Build the default clicker and run it until the stop key is pressed."""
    build_default_clicker(config).run()
