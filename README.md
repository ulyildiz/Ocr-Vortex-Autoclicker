# Vortex Auto-Clicker

[![CI](https://github.com/your-username/vortex-autoclicker/actions/workflows/ci.yml/badge.svg)](https://github.com/your-username/vortex-autoclicker/actions/workflows/ci.yml)
![Python](https://img.shields.io/badge/python-3.10%2B-blue)
![Platform](https://img.shields.io/badge/platform-Windows-lightgrey)
[![License: MIT](https://img.shields.io/badge/license-MIT-green)](LICENSE)

An OCR-based auto-clicker for **Vortex** + **Nexus Mods** free-tier downloads.

Installing a large collection as a free Nexus Mods user means clicking the same
buttons hundreds of times. This tool reads the text on your screen with OCR and
clicks the buttons **by their label**. You don't need screenshots or image
templates, and it keeps working after theme or resolution changes.

---

## Table of contents

- [How it works](#how-it-works)
- [Requirements](#requirements)
- [Installation](#installation)
- [Usage](#usage)
- [Command-line options](#command-line-options)
- [Using it as a library](#using-it-as-a-library)
- [Troubleshooting](#troubleshooting)
- [Development](#development)
- [Project structure](#project-structure)
- [AI-generated code](#ai-generated-code)
- [Disclaimer](#disclaimer)
- [License](#license)

## How it works

For every mod in the queue the clicker repeats this cycle:

| # | Where   | Action                                                                |
|---|---------|-----------------------------------------------------------------------|
| 1 | Vortex  | Click **Install** *(optional, see `--no-install`)*                    |
| 2 | Vortex  | Click **Download manually**                                           |
| 3 | Browser | Click **Slow download**                                               |
| 4 | Windows | Wait until Vortex takes focus (download handed over), close the Nexus **tab** with `Ctrl+W` and bring Vortex back to the front |

Step 4 does not need to *see* the tab. It finds the browser window by its title
(`... Nexus ...`), focuses it, sends `Ctrl+W` (which closes only the active
tab, never the whole browser) and then refocuses Vortex so the next popup is
visible to OCR.

When several buttons are visible at the same time, the order of the steps sets
the priority. Each step has a **cooldown** so a button is not clicked twice
while the UI is still changing.

## Requirements

- **Windows 10/11.** Closing the tab uses the Win32 API. The click loop also
  runs on other systems, but there tab closing is turned off automatically.
- **Python 3.10+**
- Vortex and the browser must use an **English** UI.
- The browser's `nxm://` handler prompt must be turned off (tick
  *"Always allow"* once), so the download is handed to Vortex without a popup.
- Keep **at least one other tab** open in the browser window. Closing the last
  tab of a window closes the whole window.

> [!NOTE]
> The `keyboard` package installs a global keyboard hook. On some systems this
> needs an elevated (administrator) terminal.

## Installation

### From source (recommended for now)

```bash
git clone https://github.com/your-username/vortex-autoclicker.git
cd vortex-autoclicker
python -m venv .venv
.venv\Scripts\activate
pip install .
```

### As an isolated tool with pipx

```bash
pipx install git+https://github.com/your-username/vortex-autoclicker.git
```

Both methods install the `vortex-autoclicker` command together with its
dependencies: `rapidocr`, `onnxruntime`, `pyautogui`, `keyboard`, `pillow`,
`numpy` and `opencv-python`.

## Usage

1. Open Vortex and start installing a collection.
2. Open your browser and log in to Nexus Mods.
3. Run:

   ```bash
   vortex-autoclicker
   ```

   or, equivalently:

   ```bash
   python -m vortex_autoclicker
   ```

4. Leave the screen alone while it works. The first scan takes a few seconds
   while the OCR models load.

**Stopping:**

- Press **ESC** (or the key set with `--stop-key`).
- **Failsafe:** move the mouse quickly into a corner of the screen (a PyAutoGUI feature).

### Examples

```bash
# The collection opens the "Download mod" popup by itself: don't click "Install"
vortex-autoclicker --no-install

# Keep the Nexus tabs open
vortex-autoclicker --no-close-page

# Your browser title shows "nexusmods.com" instead of "Nexus"
vortex-autoclicker --browser-keyword nexusmods

# Looser matching for blurry or scaled UIs, and debug logging
vortex-autoclicker --threshold 0.8 --verbose

# Use your own buttons (replaces the defaults; order = priority)
vortex-autoclicker -s "Slow download:2" -s "Download manually:3" -s "Continue:1"

# Show which steps would be used, without clicking anything
vortex-autoclicker --no-install --list-steps
```

## Command-line options

| Option | Default | Description |
|---|---|---|
| `-s`, `--step LABEL[:COOLDOWN]` | see below | Button label to click, with an optional cooldown in seconds (default 2). Can be repeated; order = priority. **Replaces** the default steps. |
| `--no-install` | off | Leave out the `Install` step. |
| `-t`, `--threshold FLOAT` | `0.9` | Minimum similarity (0–1] between OCR text and a label. |
| `-i`, `--poll-interval SEC` | `0.3` | Extra pause between scans. OCR itself takes about 0.5–1.5 s. |
| `--list-steps` | off | Print the effective steps and exit. |
| `--no-close-page` | off | Don't close the Nexus browser tab after the hand-over. |
| `--trigger-label LABEL` | `Slow download` | Clicking this label starts the tab-closing routine. |
| `--handoff-timeout SEC` | `5.0` | Max time to wait for Vortex to take focus. |
| `--close-grace SEC` | `0.5` | Extra pause after Vortex took focus, before closing the tab. |
| `--browser-keyword TEXT` | `nexus` | The browser window title must contain this (case-insensitive). |
| `--vortex-keyword TEXT` | `vortex` | The Vortex window title must contain this (case-insensitive). |
| `--stop-key KEY` | `esc` | Key that stops the clicker (any name the `keyboard` package accepts). |
| `-v`, `--verbose` | off | Debug output (e.g. number of OCR results per scan). |
| `-q`, `--quiet` | off | Only warnings and errors. |
| `--version` | | Print the version and exit. |
| `-h`, `--help` | | Show help and exit. |

Default steps: `Slow download` (2 s) → `Download manually` (3 s) → `Install` (5 s).

**Exit codes:** `0` success / stopped, `1` runtime error (e.g. a missing
dependency), `2` invalid arguments, `130` interrupted with `Ctrl+C`.

## Using it as a library

Importing the package is cheap. The OCR engine and the input libraries are only
loaded when the clicker is built.

```python
from vortex_autoclicker import Config, Step, run

config = Config(
    steps=(Step("Slow download", 2.0), Step("Download manually", 3.0)),
    match_threshold=0.85,
    close_page=False,
)
run(config)  # blocks until the stop key is pressed
```

The main loop has no hidden side effects. Everything is injected, so you can
plug in your own screen reader, click function or stop condition:

```python
from vortex_autoclicker import AutoClicker, Config, ScreenReader

clicker = AutoClicker(
    Config(),
    read_screen=ScreenReader(),               # or any callable returning TextItems
    click=lambda x, y: print("click", x, y),  # dry run: only log clicks
    should_stop=lambda: False,
)
clicker.scan_once()  # a single scan; returns the clicked label or None
```

Useful building blocks:

| Name | Purpose |
|---|---|
| `Config`, `Step`, `DEFAULT_STEPS` | Immutable, validated settings. |
| `AutoClicker` | The scan-and-click loop (`scan_once()`, `run()`). |
| `build_default_clicker(config)` / `run(config)` | Wire everything to the real screen, mouse and keyboard. |
| `ScreenReader` | Screen capture + RapidOCR → `list[TextItem]`. |
| `find_button(items, label, threshold)` | Pure fuzzy label matching. |
| `TabCloser` | The "close the Nexus tab after hand-over" routine. |
| `VortexAutoClickerError` | Base class of every error raised by the package. |

## Troubleshooting

| Problem | Fix |
|---|---|
| `Required module '...' is not installed` | Run `pip install .` again inside the right virtual environment. |
| Buttons are found but not clicked / clicked in the wrong place | Display scaling other than 100 % can shift coordinates. Try 100 % scaling, or make sure Python is DPI-aware. |
| Buttons are not detected | Run with `-v`. Lower `--threshold` a little (e.g. `0.8`) and check that the UI is in English. |
| `Close page: no window with 'nexus' in its title` | The log lists every open window title. Pick a keyword from your browser's title and pass it with `--browser-keyword`. |
| The whole browser closes | That was the last tab in the window. Keep another tab open. |
| ESC does nothing | Run the terminal as administrator (the global keyboard hook may need it). |

## Development

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -e ".[dev]"

pytest                 # unit tests (no screen, mouse or Windows needed)
pytest --cov           # with coverage
ruff check .           # lint
ruff format .          # format
mypy                   # static type check (strict)
```

The tests replace every side effect (screen capture, OCR engine, mouse,
keyboard, Win32 windows, time) with fakes, so they run fast and on any OS.

Contributions are welcome. Please open an issue first for larger changes, and
make sure `pytest`, `ruff check .` and `mypy` pass before you submit a pull
request.

## Project structure

```
vortex-autoclicker/
├── .github/workflows/ci.yml     # Lint, type check and tests on Windows
├── src/vortex_autoclicker/
│   ├── __init__.py              # Public API and __version__
│   ├── __main__.py              # python -m vortex_autoclicker
│   ├── cli.py                   # argparse CLI
│   ├── clicker.py               # AutoClicker loop + default wiring
│   ├── config.py                # Config / Step dataclasses, defaults
│   ├── exceptions.py            # Exception hierarchy
│   ├── handoff.py               # Close the Nexus tab after hand-over
│   ├── matching.py              # Fuzzy label matching (pure)
│   ├── ocr.py                   # Screen capture + RapidOCR parsing
│   ├── utils.py                 # Platform check, lazy imports
│   ├── windows.py               # Win32 window discovery / focus
│   └── py.typed                 # PEP 561 marker
├── tests/                       # pytest suite
├── CHANGELOG.md
├── LICENSE
├── pyproject.toml
└── README.md
```

## AI-generated code

This project was made with AI. The code, tests and documentation were written
by an AI assistant ([Claude](https://www.anthropic.com/claude) by Anthropic,
using Claude Code). It may still contain mistakes, so read the code before you
rely on it and report problems through the issue tracker.

## Disclaimer

This project is not affiliated with or endorsed by Nexus Mods or Black Tree
Gaming Ltd. It only clicks the same buttons you would click yourself, including
the regular *Slow download* button, and does not bypass any wait time,
rate limit or premium feature. You are responsible for following the
[Nexus Mods Terms of Service](https://help.nexusmods.com/article/18-terms-of-service).
Use at your own risk.

## License

[MIT](LICENSE)
