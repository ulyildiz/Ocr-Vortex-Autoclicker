"""Command-line interface: ``vortex-autoclicker`` / ``python -m vortex_autoclicker``."""

from __future__ import annotations

import argparse
import logging
from collections.abc import Sequence

from vortex_autoclicker.config import DEFAULT_STEPS, Config, Step
from vortex_autoclicker.exceptions import ConfigError, VortexAutoClickerError
from vortex_autoclicker.matching import normalize

logger = logging.getLogger("vortex_autoclicker")

PROG = "vortex-autoclicker"
DEFAULT_STEP_COOLDOWN = 2.0
EXIT_OK = 0
EXIT_ERROR = 1
EXIT_INTERRUPTED = 130


def parse_step(value: str) -> Step:
    """Parse a ``LABEL[:COOLDOWN]`` command-line value into a :class:`Step`.

    The part after the *last* colon is used as the cooldown only if it is a
    number, so labels that contain colons still work.

    Raises:
        argparse.ArgumentTypeError: If the value is invalid.
    """
    label, sep, cooldown_text = value.rpartition(":")
    cooldown = DEFAULT_STEP_COOLDOWN
    if sep and label.strip():
        try:
            cooldown = float(cooldown_text)
        except ValueError:
            label = value
    else:
        label = value
    try:
        return Step(label.strip(), cooldown)
    except ConfigError as exc:
        raise argparse.ArgumentTypeError(str(exc)) from exc


def _non_negative_float(value: str) -> float:
    try:
        number = float(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(f"not a number: {value!r}") from exc
    if number < 0:
        raise argparse.ArgumentTypeError(f"must be >= 0, got {number}")
    return number


def _threshold(value: str) -> float:
    number = _non_negative_float(value)
    if not 0.0 < number <= 1.0:
        raise argparse.ArgumentTypeError(f"must be in the range (0, 1], got {number}")
    return number


def build_parser() -> argparse.ArgumentParser:
    """Create the argument parser."""
    from vortex_autoclicker import __version__

    defaults = Config()
    parser = argparse.ArgumentParser(
        prog=PROG,
        description=(
            "Automate Vortex + Nexus Mods free downloads by reading button labels "
            "on screen with OCR and clicking them. Press the stop key (default: ESC) "
            "or move the mouse into a screen corner to stop."
        ),
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")

    steps = parser.add_argument_group("buttons")
    steps.add_argument(
        "-s",
        "--step",
        dest="steps",
        action="append",
        type=parse_step,
        metavar="LABEL[:COOLDOWN]",
        help=(
            "Button label to click, optionally with a cooldown in seconds "
            f"(default {DEFAULT_STEP_COOLDOWN:g}). Repeat to add more; order = priority. "
            "Replaces the default steps: "
            + ", ".join(f"'{s.label}:{s.cooldown:g}'" for s in DEFAULT_STEPS)
        ),
    )
    steps.add_argument(
        "--no-install",
        action="store_true",
        help="Do not click 'Install' (use when the collection opens the download popup itself).",
    )
    steps.add_argument(
        "-t",
        "--threshold",
        type=_threshold,
        default=defaults.match_threshold,
        help="How closely OCR text must match a label (0-1].",
    )
    steps.add_argument(
        "-i",
        "--poll-interval",
        type=_non_negative_float,
        default=defaults.poll_interval,
        help="Extra pause between screen scans in seconds.",
    )
    steps.add_argument(
        "--list-steps",
        action="store_true",
        help="Print the effective steps and exit without clicking anything.",
    )

    closing = parser.add_argument_group("closing the Nexus tab (Windows only)")
    closing.add_argument(
        "--no-close-page",
        dest="close_page",
        action="store_false",
        help="Keep the Nexus browser tab open after the download was handed over.",
    )
    closing.add_argument(
        "--trigger-label",
        default=defaults.close_trigger_label,
        help="Clicking this label triggers closing the tab.",
    )
    closing.add_argument(
        "--handoff-timeout",
        type=_non_negative_float,
        default=defaults.handoff_timeout,
        help="Max seconds to wait for Vortex to take focus.",
    )
    closing.add_argument(
        "--close-grace",
        type=_non_negative_float,
        default=defaults.close_grace,
        help="Extra pause after Vortex took focus, before closing the tab.",
    )
    closing.add_argument(
        "--browser-keyword",
        default=defaults.browser_title_keyword,
        help="The browser window title must contain this (case-insensitive).",
    )
    closing.add_argument(
        "--vortex-keyword",
        default=defaults.vortex_title_keyword,
        help="The Vortex window title must contain this (case-insensitive).",
    )

    general = parser.add_argument_group("general")
    general.add_argument(
        "--stop-key", default=defaults.stop_key, help="Key that stops the clicker."
    )
    verbosity = general.add_mutually_exclusive_group()
    verbosity.add_argument("-v", "--verbose", action="store_true", help="Show debug output.")
    verbosity.add_argument(
        "-q", "--quiet", action="store_true", help="Only show warnings and errors."
    )
    return parser


def config_from_args(args: argparse.Namespace) -> Config:
    """Build a :class:`Config` from parsed command-line arguments.

    Raises:
        ConfigError: If the resulting configuration is invalid.
    """
    steps: tuple[Step, ...] = tuple(args.steps) if args.steps else DEFAULT_STEPS
    if args.no_install:
        steps = tuple(step for step in steps if normalize(step.label) != "install")
    return Config(
        steps=steps,
        match_threshold=args.threshold,
        poll_interval=args.poll_interval,
        close_page=args.close_page,
        close_trigger_label=args.trigger_label,
        handoff_timeout=args.handoff_timeout,
        close_grace=args.close_grace,
        browser_title_keyword=args.browser_keyword,
        vortex_title_keyword=args.vortex_keyword,
        stop_key=args.stop_key,
    )


def configure_logging(verbose: bool = False, quiet: bool = False) -> None:
    """Set up console logging for CLI use."""
    level = logging.DEBUG if verbose else logging.WARNING if quiet else logging.INFO
    logging.basicConfig(format="%(asctime)s %(levelname)-7s %(message)s", datefmt="%H:%M:%S")
    logging.getLogger("vortex_autoclicker").setLevel(level)


def _is_pyautogui_failsafe(exc: BaseException) -> bool:
    # Checked by name so the CLI does not have to import PyAutoGUI eagerly.
    return type(exc).__name__ == "FailSafeException"


def main(argv: Sequence[str] | None = None) -> int:
    """Run the command-line interface.

    Args:
        argv: Arguments without the program name; defaults to ``sys.argv[1:]``.

    Returns:
        The process exit code.
    """
    parser = build_parser()
    args = parser.parse_args(argv)
    configure_logging(verbose=args.verbose, quiet=args.quiet)

    try:
        config = config_from_args(args)
    except ConfigError as exc:
        parser.error(str(exc))

    if args.list_steps:
        for index, step in enumerate(config.steps, start=1):
            print(f"{index}. {step.label!r} (cooldown {step.cooldown:g}s)")
        return EXIT_OK

    from vortex_autoclicker.clicker import build_default_clicker

    try:
        build_default_clicker(config).run()
    except KeyboardInterrupt:
        logger.info("Interrupted.")
        return EXIT_INTERRUPTED
    except VortexAutoClickerError as exc:
        logger.error("%s", exc)
        return EXIT_ERROR
    except Exception as exc:
        if _is_pyautogui_failsafe(exc):
            logger.warning("PyAutoGUI failsafe triggered (mouse in a screen corner). Stopped.")
            return EXIT_OK
        raise
    return EXIT_OK
