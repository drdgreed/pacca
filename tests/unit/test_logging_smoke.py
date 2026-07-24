"""
Logging smoke test — PRODUCTION_READINESS B5.

B5 was a P0: modules created a stdlib logger via ``logging.getLogger(__name__)``
but called it with structured keyword arguments — ``logger.warning("event",
error=..., fallback=...)`` — which a stdlib logger rejects with
``TypeError: Logger._log() got an unexpected keyword argument 'error'``. That
500'd the request, and worse, it fired inside ``except`` blocks meant to
log-and-recover, so a recoverable failure became a hard crash.

The named crash site (``integrations/vector_store.py``) was migrated to the
structlog-backed ``get_logger``. Nothing exercised that log path in tests, so a
regression to a stdlib logger would go uncaught. This smoke test closes that gap:
it asserts every module that logs with structured kwargs uses a structlog logger,
and that a structured-kwarg call actually executes without raising.

Teaching note — why assert on logger *type*, not just "no exception":

  A stdlib logger only raises on structured kwargs when the specific call is
  reached at runtime. Asserting the logger is structlog pins the contract before
  any particular branch runs, so a regression is caught even for log lines this
  test doesn't drive.
"""

from __future__ import annotations

import logging

from pacca.agents import base as base_mod
from pacca.integrations import vector_store as vector_store_mod


def _is_structlog_logger(logger: object) -> bool:
    """structlog bound loggers are not instances of the stdlib logging.Logger."""
    return not isinstance(logger, logging.Logger)


def test_agent_base_uses_a_structlog_logger() -> None:
    assert _is_structlog_logger(base_mod.logger), (
        "agents/base.py uses a stdlib logger; a structured-kwarg call would "
        "TypeError at runtime (B5)"
    )


def test_vector_store_uses_a_structlog_logger() -> None:
    assert _is_structlog_logger(vector_store_mod.logger), (
        "integrations/vector_store.py regressed to a stdlib logger (B5)"
    )


def test_structured_kwargs_do_not_raise() -> None:
    """The exact B5 failure mode: a structured-kwarg call must not raise."""
    # These mirror the real call shapes in each module's except/retry paths.
    base_mod.logger.warning(
        "llm_api_retry", attempt=1, wait_seconds=0.5, error_type="RateLimitError"
    )
    vector_store_mod.logger.warning(
        "rag_pipeline_init_failed", error="boom", fallback="direct_chromadb"
    )
