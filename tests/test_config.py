from __future__ import annotations

import pytest

from vortex_autoclicker.config import DEFAULT_STEPS, Config, Step
from vortex_autoclicker.exceptions import ConfigError


def test_defaults_are_valid() -> None:
    config = Config()
    assert config.steps == DEFAULT_STEPS
    assert [s.label for s in config.steps] == ["Slow download", "Download manually", "Install"]


def test_steps_list_is_stored_as_tuple() -> None:
    config = Config(steps=[Step("Install", 1.0)])  # type: ignore[arg-type]
    assert isinstance(config.steps, tuple)


@pytest.mark.parametrize(
    "kwargs",
    [
        {"steps": ()},
        {"match_threshold": 0.0},
        {"match_threshold": 1.5},
        {"poll_interval": -1},
        {"handoff_timeout": -0.1},
        {"browser_title_keyword": " "},
        {"browser_title_keyword": "Vortex", "vortex_title_keyword": "vortex"},
        {"stop_key": ""},
    ],
)
def test_invalid_config_raises(kwargs: dict[str, object]) -> None:
    with pytest.raises(ConfigError):
        Config(**kwargs)  # type: ignore[arg-type]


@pytest.mark.parametrize(("label", "cooldown"), [("", 1.0), ("   ", 1.0), ("Install", -1.0)])
def test_invalid_step_raises(label: str, cooldown: float) -> None:
    with pytest.raises(ConfigError):
        Step(label, cooldown)


def test_config_error_is_a_value_error() -> None:
    with pytest.raises(ValueError):
        Step("", 0)
