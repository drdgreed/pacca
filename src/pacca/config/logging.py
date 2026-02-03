"""
Structured logging configuration for the PACCA system.

Uses structlog for structured, contextual logging with JSON output
suitable for production log aggregation systems.
"""

import logging
import sys
from typing import Any

import structlog
from structlog.types import EventDict, Processor

from pacca.config.settings import get_settings


def add_app_context(
    logger: logging.Logger, method_name: str, event_dict: EventDict
) -> EventDict:
    """Add application context to every log entry."""
    settings = get_settings()
    event_dict["app"] = settings.app_name
    event_dict["env"] = settings.app_env
    return event_dict


def drop_color_message_key(
    logger: logging.Logger, method_name: str, event_dict: EventDict
) -> EventDict:
    """Remove color_message key that structlog adds for console output."""
    event_dict.pop("color_message", None)
    return event_dict


def setup_logging(
    json_logs: bool | None = None,
    log_level: str | None = None,
) -> None:
    """
    Configure structured logging for the application.

    Args:
        json_logs: Whether to output JSON logs. If None, determined by environment.
        log_level: Log level string. If None, uses settings.
    """
    settings = get_settings()

    # Determine log format based on environment if not specified
    if json_logs is None:
        json_logs = settings.is_production

    # Determine log level
    if log_level is None:
        log_level = settings.log_level

    # Shared processors for all log entries
    shared_processors: list[Processor] = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.UnicodeDecoder(),
        add_app_context,
    ]

    if json_logs:
        # Production: JSON output
        shared_processors.append(drop_color_message_key)
        shared_processors.append(structlog.processors.format_exc_info)
        shared_processors.append(structlog.processors.JSONRenderer())
    else:
        # Development: colored console output
        shared_processors.append(structlog.dev.ConsoleRenderer(colors=True))

    # Configure structlog
    structlog.configure(
        processors=shared_processors,
        wrapper_class=structlog.stdlib.BoundLogger,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )

    # Configure standard library logging
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=getattr(logging, log_level.upper()),
    )

    # Suppress noisy loggers
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)


def get_logger(name: str | None = None) -> structlog.stdlib.BoundLogger:
    """
    Get a structured logger instance.

    Args:
        name: Logger name. If None, uses the calling module's name.

    Returns:
        A bound structlog logger.

    Example:
        logger = get_logger(__name__)
        logger.info("processing_request", request_id="123", patient_id="P456")
    """
    return structlog.get_logger(name)


class LogContext:
    """
    Context manager for adding temporary context to logs.

    Example:
        with LogContext(request_id="123", user_id="U456"):
            logger.info("processing")  # Includes request_id and user_id
    """

    def __init__(self, **kwargs: Any) -> None:
        self.context = kwargs
        self._token: Any = None

    def __enter__(self) -> "LogContext":
        self._token = structlog.contextvars.bind_contextvars(**self.context)
        return self

    def __exit__(self, *args: Any) -> None:
        structlog.contextvars.unbind_contextvars(*self.context.keys())


def bind_request_context(
    request_id: str,
    **additional_context: Any,
) -> None:
    """
    Bind request-scoped context to all logs in the current context.

    Typically called at the start of request processing.

    Args:
        request_id: Unique request identifier
        **additional_context: Additional context to bind
    """
    structlog.contextvars.bind_contextvars(
        request_id=request_id,
        **additional_context,
    )


def clear_request_context() -> None:
    """Clear all request-scoped context. Called at end of request."""
    structlog.contextvars.clear_contextvars()
