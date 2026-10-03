# Changelog

All notable changes to this project are documented in this file.
The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and the
project adheres to [Semantic Versioning](https://semver.org/).

## [Unreleased]

## [0.1.0] - 2026-10-03

### Added
- First packaged release, restructured from the single `vortex_autoclicker_ocr.py` script.
- `vortex-autoclicker` console command and `python -m vortex_autoclicker` entry point.
- Command-line options for steps, match threshold, poll interval, tab-closing behaviour,
  window-title keywords, stop key and verbosity.
- Importable library API (`Config`, `Step`, `AutoClicker`, `run`, ...).
- Unit tests that run without a screen, mouse, keyboard or Windows.
