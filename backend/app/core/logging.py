"""Logging configuration.

Application logs must never contain patient data or secrets
(docs/05_CONTRAINTES_SECURITE.md). This sets up a plain, level-controlled
logger; structured logging and PHI-scrubbing filters are added in later phases.
"""

from __future__ import annotations

import logging

from app.core.config import get_settings

_LOG_FORMAT = "%(asctime)s %(levelname)-8s %(name)s — %(message)s"


def configure_logging() -> None:
    """Configure root logging from settings (idempotent)."""
    settings = get_settings()
    level = getattr(logging, settings.log_level.upper(), logging.INFO)
    logging.basicConfig(level=level, format=_LOG_FORMAT)


def get_logger(name: str) -> logging.Logger:
    """Return a named logger."""
    return logging.getLogger(name)
