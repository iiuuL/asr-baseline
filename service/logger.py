"""Minimal logging entrypoints for the service layer.

This module currently exposes a plain standard-library logger so we can
gradually replace `print`/`traceback.print_exc()` style output later.
"""

import logging


DEFAULT_LOGGER_NAME = "service"


def get_logger(name: str = DEFAULT_LOGGER_NAME) -> logging.Logger:
    """Return a configured logger instance.

    The setup is intentionally conservative:
    - no handler customization yet
    - no global logging side effects
    - safe to import without changing current behavior
    """

    return logging.getLogger(name)


__all__ = ["DEFAULT_LOGGER_NAME", "get_logger"]
