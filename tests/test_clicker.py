from __future__ import annotations

from collections.abc import Sequence

from conftest import FakeClock
from vortex_autoclicker.clicker import AutoClicker
from vortex_autoclicker.config import Config, Step
from vortex_autoclicker.matching import TextItem


class Recorder:
    def __init__(self) -> None:
        self.clicks: list[tuple[float, float]] = []
        self.triggers = 0

    def click(self, x: float, y: float) -> None:
        self.clicks.append((x, y))

    def trigger(self) -> None:
        self.triggers += 1


def make_clicker(
    screen: Sequence[TextItem],
    clock: FakeClock,
    recorder: Recorder,
    config: Config | None = None,
    stop_after: int = 1,
) -> AutoClicker:
    checks = {"n": 0}

    def should_stop() -> bool:
        checks["n"] += 1
        return checks["n"] > stop_after

    return AutoClicker(
        config or Config(),
        read_screen=lambda: list(screen),
        click=recorder.click,
        should_stop=should_stop,
        after_trigger_click=recorder.trigger,
        clock=clock,
        sleep=clock.sleep,
    )


def test_clicks_highest_priority_button(clock: FakeClock) -> None:
    rec = Recorder()
    screen = [TextItem("Install", 1, 1), TextItem("Download manually", 2, 2)]
    clicker = make_clicker(screen, clock, rec)

    assert clicker.scan_once() == "Download manually"
    assert rec.clicks == [(2, 2)]


def test_only_one_click_per_scan(clock: FakeClock) -> None:
    rec = Recorder()
    screen = [TextItem("Install", 1, 1), TextItem("Download manually", 2, 2)]
    make_clicker(screen, clock, rec).scan_once()
    assert len(rec.clicks) == 1


def test_nothing_to_click_returns_none(clock: FakeClock) -> None:
    rec = Recorder()
    assert make_clicker([TextItem("Settings", 1, 1)], clock, rec).scan_once() is None
    assert rec.clicks == []


def test_cooldown_falls_through_to_next_step(clock: FakeClock) -> None:
    rec = Recorder()
    screen = [TextItem("Download manually", 2, 2), TextItem("Install", 1, 1)]
    clicker = make_clicker(screen, clock, rec)

    assert clicker.scan_once() == "Download manually"
    clock.advance(1.0)  # cooldown for "Download manually" is 3 s
    assert clicker.scan_once() == "Install"
    clock.advance(2.5)
    assert clicker.scan_once() == "Download manually"


def test_trigger_label_runs_callback(clock: FakeClock) -> None:
    rec = Recorder()
    clicker = make_clicker([TextItem("Slow download", 3, 3)], clock, rec)
    clicker.scan_once()
    assert rec.triggers == 1


def test_non_trigger_label_does_not_run_callback(clock: FakeClock) -> None:
    rec = Recorder()
    make_clicker([TextItem("Install", 3, 3)], clock, rec).scan_once()
    assert rec.triggers == 0


def test_custom_steps_and_threshold(clock: FakeClock) -> None:
    rec = Recorder()
    config = Config(steps=(Step("Continue", 0.0),), match_threshold=1.0)
    screen = [TextItem("Continu", 1, 1), TextItem("Continue", 9, 9)]
    clicker = make_clicker(screen, clock, rec, config)
    clicker.scan_once()
    assert rec.clicks == [(9, 9)]


def test_run_loops_until_stopped_and_sleeps_between_scans(clock: FakeClock) -> None:
    rec = Recorder()
    config = Config(steps=(Step("Install", 0.0),), poll_interval=0.25)
    clicker = make_clicker([TextItem("Install", 1, 1)], clock, rec, config, stop_after=3)

    clicker.run()

    assert len(rec.clicks) == 3
    assert clock.sleeps == [0.25, 0.25, 0.25]
