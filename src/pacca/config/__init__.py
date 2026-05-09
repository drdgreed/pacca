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
from pacca.config.tracing import configure_tracing, get_current_trace_id, get_tracer

__all__ = [
    "LogContext",
    # Settings
    "Settings",
    "bind_request_context",
    "clear_request_context",
    # Tracing
    "configure_tracing",
    "get_anthropic_api_key",
    "get_current_trace_id",
    "get_logger",
    "get_settings",
    "get_tracer",
    # Logging
    "setup_logging",
]
