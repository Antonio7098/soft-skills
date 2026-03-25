"""Structured logging configuration."""

from __future__ import annotations

import logging
from typing import cast

import structlog


def configure_logging(log_level: str) -> None:
    """Configure global JSON logging."""

    resolved_level = logging.getLevelName(log_level.upper())
    if not isinstance(resolved_level, int):
        resolved_level = logging.INFO

    logging.basicConfig(level=resolved_level, format="%(message)s")
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.stdlib.add_log_level,
            structlog.stdlib.add_logger_name,
            structlog.processors.TimeStamper(fmt="iso", utc=True),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(resolved_level),
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )


def get_logger(name: str) -> structlog.stdlib.BoundLogger:
    """Return a structured logger."""

    return cast(structlog.stdlib.BoundLogger, structlog.get_logger(name))
