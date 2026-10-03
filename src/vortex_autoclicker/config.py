"""Configuration objects and default values."""

from __future__ import annotations

from dataclasses import dataclass

from vortex_autoclicker.exceptions import ConfigError


@dataclass(frozen=True)
class Step:
    """A button the clicker looks for on screen.

    Attributes:
        label: The visible text of the button, matched fuzzily and
            case-insensitively against the OCR output.
        cooldown: Minimum number of seconds before the same label may be
            clicked again. Prevents double-clicks while the UI is changing.
    """

    label: str
    cooldown: float

    def __post_init__(self) -> None:
        if not self.label.strip():
            raise ConfigError("Step label must not be empty.")
        if self.cooldown < 0:
            raise ConfigError(
                f"Cooldown for step {self.label!r} must be >= 0, got {self.cooldown}."
            )


#: Default steps. Order equals priority when several buttons are visible at once.
#: ``Install`` is optional: drop it if the collection already opens the
#: "Download mod" popup by itself (see ``--no-install`` on the CLI).
DEFAULT_STEPS: tuple[Step, ...] = (
    Step("Slow download", 2.0),
    Step("Download manually", 3.0),
    Step("Install", 5.0),
)

#: Label whose click hands the download over to Vortex (and triggers tab closing).
DEFAULT_CLOSE_TRIGGER_LABEL = "Slow download"


@dataclass(frozen=True)
class Config:
    """Runtime settings for :class:`~vortex_autoclicker.clicker.AutoClicker`.

    Attributes:
        steps: Buttons to click, in priority order.
        match_threshold: Minimum similarity (0-1] between OCR text and a label.
        poll_interval: Extra pause between screen scans, in seconds. OCR itself
            already takes roughly 0.5-1.5 s per scan.
        close_page: Close the Nexus browser tab after the download was handed
            over to Vortex (Windows only).
        close_trigger_label: Clicking this label triggers the tab-closing logic.
        handoff_timeout: Max seconds to wait for Vortex to take window focus.
        close_grace: Extra pause after Vortex took focus, before closing the tab.
        browser_title_keyword: The browser window title must contain this.
        vortex_title_keyword: The Vortex window title must contain this.
        stop_key: Keyboard key that stops the main loop.
    """

    steps: tuple[Step, ...] = DEFAULT_STEPS
    match_threshold: float = 0.9
    poll_interval: float = 0.3
    close_page: bool = True
    close_trigger_label: str = DEFAULT_CLOSE_TRIGGER_LABEL
    handoff_timeout: float = 5.0
    close_grace: float = 0.5
    browser_title_keyword: str = "nexus"
    vortex_title_keyword: str = "vortex"
    stop_key: str = "esc"

    def __post_init__(self) -> None:
        # Accept any iterable (e.g. a list) but store an immutable tuple.
        object.__setattr__(self, "steps", tuple(self.steps))
        if not self.steps:
            raise ConfigError("At least one step is required.")
        if not 0.0 < self.match_threshold <= 1.0:
            raise ConfigError(
                f"match_threshold must be in the range (0, 1], got {self.match_threshold}."
            )
        for name in ("poll_interval", "handoff_timeout", "close_grace"):
            if getattr(self, name) < 0:
                raise ConfigError(f"{name} must be >= 0, got {getattr(self, name)}.")
        for name in ("browser_title_keyword", "vortex_title_keyword", "stop_key"):
            if not getattr(self, name).strip():
                raise ConfigError(f"{name} must not be empty.")
        if self.browser_title_keyword.lower() == self.vortex_title_keyword.lower():
            raise ConfigError("browser_title_keyword and vortex_title_keyword must differ.")
