from __future__ import annotations

import argparse

import pytest

from vortex_autoclicker import __version__
from vortex_autoclicker.cli import build_parser, config_from_args, main, parse_step
from vortex_autoclicker.config import DEFAULT_STEPS, Step


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("Install", Step("Install", 2.0)),
        ("Install:5", Step("Install", 5.0)),
        ("Slow download:0.5", Step("Slow download", 0.5)),
        ("Note: read me", Step("Note: read me", 2.0)),
        ("Step: two:1.5", Step("Step: two", 1.5)),
    ],
)
def test_parse_step(value: str, expected: Step) -> None:
    assert parse_step(value) == expected


@pytest.mark.parametrize("value", ["", "   ", "Install:-1"])
def test_parse_step_rejects_invalid(value: str) -> None:
    with pytest.raises(argparse.ArgumentTypeError):
        parse_step(value)


def config_for(*argv: str):  # type: ignore[no-untyped-def]
    return config_from_args(build_parser().parse_args(list(argv)))


def test_defaults() -> None:
    config = config_for()
    assert config.steps == DEFAULT_STEPS
    assert config.close_page is True


def test_custom_steps_replace_defaults() -> None:
    config = config_for("-s", "Continue:1", "-s", "Done")
    assert config.steps == (Step("Continue", 1.0), Step("Done", 2.0))


def test_no_install_drops_install_step() -> None:
    assert "Install" not in [s.label for s in config_for("--no-install").steps]


def test_options_are_mapped() -> None:
    config = config_for(
        "--threshold",
        "0.8",
        "--poll-interval",
        "1",
        "--no-close-page",
        "--browser-keyword",
        "Firefox",
        "--stop-key",
        "f12",
    )
    assert config.match_threshold == 0.8
    assert config.poll_interval == 1.0
    assert config.close_page is False
    assert config.browser_title_keyword == "Firefox"
    assert config.stop_key == "f12"


@pytest.mark.parametrize("argv", [["--threshold", "0"], ["--threshold", "2"], ["-i", "-1"]])
def test_invalid_values_exit_with_usage_error(argv: list[str]) -> None:
    with pytest.raises(SystemExit) as exc_info:
        main(argv)
    assert exc_info.value.code == 2


def test_removing_every_step_is_a_usage_error() -> None:
    with pytest.raises(SystemExit) as exc_info:
        main(["-s", "Install", "--no-install"])
    assert exc_info.value.code == 2


def test_list_steps_prints_and_exits(capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["--list-steps", "--no-install"]) == 0
    out = capsys.readouterr().out
    assert "'Slow download'" in out
    assert "Install" not in out


def test_version(capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit) as exc_info:
        main(["--version"])
    assert exc_info.value.code == 0
    assert __version__ in capsys.readouterr().out
