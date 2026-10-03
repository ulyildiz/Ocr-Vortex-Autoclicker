"""Exception hierarchy used throughout the package.

Every error raised on purpose by this package derives from
:class:`VortexAutoClickerError`, so callers can catch a single base class.
"""

from __future__ import annotations


class VortexAutoClickerError(Exception):
    """Base class for all errors raised by ``vortex_autoclicker``."""


class ConfigError(VortexAutoClickerError, ValueError):
    """Raised when a configuration value is invalid."""


class DependencyError(VortexAutoClickerError, ImportError):
    """Raised when a required third-party package is not installed."""


class OcrError(VortexAutoClickerError):
    """Raised when the OCR engine returns output that cannot be interpreted."""


class UnsupportedPlatformError(VortexAutoClickerError):
    """Raised when a feature is used on an operating system that lacks support."""
