"""
Configuration module for PACCA.

Exports settings and logging utilities.
"""

from pacca.config.logging import (
    LogContext,
    bind_request_context,
    clear_request_context,
    get_logger,
    setup_logging,
)
from pacca.config.settings import Settings, get_anthropic_api_key, get_settings
from pacca.config.tracing import configure_tracing, get_tracer, get_current_trace_id

__all__ = [
    # Settings
    "Settings",
    "get_settings",
    "get_anthropic_api_key",
    # Logging
    "setup_logging",
    "get_logger",
    "LogContext",
    "bind_request_context",
    "clear_request_context",
    # Tracing
    "configure_tracing",
    "get_tracer",
    "get_current_trace_id",
]
