"""
core/logger/logger.py — Structured Framework Logger
=====================================================
Provides a consistent, named logger for all framework modules.

Usage:
    from core.logger.logger import get_logger
    log = get_logger(__name__)
    log.info("Browser launched: chromium")
    log.warning("Excel row not found — using defaults")
    log.error("Screenshot capture failed: %s", exc)

Log levels:
    DEBUG   — detailed internal state (disabled by default)
    INFO    — normal framework events (browser launch, report generation)
    WARNING — non-fatal issues (missing Excel row, fallback used)
    ERROR   — failures that affect test execution

Environment variable:
    LOG_LEVEL=DEBUG   — enable debug output (default: INFO)
"""

import logging
import os
from pathlib import Path

# ── Log level from environment ────────────────────────────────────────────────
_LOG_LEVEL_NAME = os.environ.get("LOG_LEVEL", "INFO").upper()
_LOG_LEVEL = getattr(logging, _LOG_LEVEL_NAME, logging.INFO)

# ── Shared formatter ──────────────────────────────────────────────────────────
_FORMATTER = logging.Formatter(
    fmt="%(asctime)s [%(levelname)-8s] %(name)s: %(message)s",
    datefmt="%H:%M:%S",
)

# ── Console handler (stdout) ──────────────────────────────────────────────────
_CONSOLE_HANDLER = logging.StreamHandler()
_CONSOLE_HANDLER.setFormatter(_FORMATTER)
_CONSOLE_HANDLER.setLevel(_LOG_LEVEL)


def get_logger(name: str) -> logging.Logger:
    """
    Return a named logger configured for the QA framework.

    Loggers are cached by Python's logging module — calling get_logger()
    with the same name always returns the same instance.

    Parameters
    ----------
    name : str — typically __name__ of the calling module
                 e.g. "core.ui.pages.login_page"

    Returns
    -------
    logging.Logger — configured logger instance
    """
    logger = logging.getLogger(name)

    # Only configure if no handlers have been added yet (avoid duplicate output)
    if not logger.handlers:
        logger.addHandler(_CONSOLE_HANDLER)
        logger.setLevel(_LOG_LEVEL)
        logger.propagate = False   # prevent double-logging via root logger

    return logger
