"""
Aggregate visibility for audit-write failures.

WHY THIS EXISTS
---------------
`AuditRepository._persist_independently` does not raise when the independent
audit write fails. That is a deliberate decision, stated in
`AuditRepository.log`'s docstring: an audit-write problem must never turn a
working request into a 500. This module does not change it.

What it changes is detectability. Before this, a failed audit write left
exactly one trace -- a `logger.error("audit_write_failed", ...)` line. So a
clinical decision could be returned to a provider with no audit row behind it,
and the only way to learn that had happened was for somebody to go looking in
the logs for an event they had no reason to suspect. The compliance posture in
docs/HIPAA_COMPLIANCE.md ("HIPAA requires that failures touching PHI be
auditable") was being maintained by log archaeology.

A monotonic counter is the right shape for the aggregate question. Alerting
systems take the derivative, so a counter answers "is audit durability failing
*now*" without the staleness a boolean flag would carry: one transient failure
at 03:00 must not leave the service reporting degraded forever, and a boolean
would.

WHAT THIS DOES NOT ANSWER
-------------------------
Which specific decisions lack an audit row. The counter is deliberately an
aggregate; per-decision truth lives in the audit table itself, and the
`correlation_id` / `request_id` on the existing error log is what joins a
specific failure back to its request. Anyone who needs "was decision X
audited?" should query audit_logs, not this.

Process-local, like the `_metrics` dict in api/routes/health.py that it is
reported alongside, and with the same limitation: it resets on restart and is
not shared across workers. That is honest for the question it answers -- a
non-zero rate on ANY worker is the signal -- and it is why the counter is
exported rather than a percentage.
"""

from __future__ import annotations

import threading
from dataclasses import dataclass
from datetime import UTC, datetime


@dataclass(frozen=True)
class AuditDurabilitySnapshot:
    """An immutable read of the counters, so callers cannot mutate live state."""

    failures_total: int
    last_failure_at: datetime | None
    last_failure_action: str | None

    @property
    def degraded(self) -> bool:
        """True if any audit write has failed since this process started."""
        return self.failures_total > 0


# A lock rather than relying on the GIL. The counter is incremented from the
# audit path, which runs inside request handling on an event loop that may be
# served by more than one thread (FastAPI runs sync dependencies in a
# threadpool), and `+=` on an int is not atomic under the free-threaded build.
# Contention is nil -- this is touched only on failure.
_lock = threading.Lock()
_failures_total = 0
_last_failure_at: datetime | None = None
_last_failure_action: str | None = None


def record_audit_write_failure(action: str | None = None) -> None:
    """Count one failed audit write. Never raises.

    Called from the failure branch of an audit write, which is itself a
    best-effort path -- so this must not be able to turn a logged failure into
    an unhandled exception. The `action` is the audit action name (e.g.
    "decision_created"), never PHI: audit action names are a fixed vocabulary
    chosen by the caller, not derived from case content.
    """
    global _failures_total, _last_failure_at, _last_failure_action
    try:
        with _lock:
            _failures_total += 1
            _last_failure_at = datetime.now(UTC)
            _last_failure_action = action
    except Exception:  # pragma: no cover - defensive; nothing here can realistically raise
        pass


def snapshot() -> AuditDurabilitySnapshot:
    """Read the counters consistently."""
    with _lock:
        return AuditDurabilitySnapshot(
            failures_total=_failures_total,
            last_failure_at=_last_failure_at,
            last_failure_action=_last_failure_action,
        )


def reset_for_tests() -> None:
    """Reset process-local state. Tests only -- there is no production reason
    to zero a monotonic counter, and doing so would erase the evidence it
    exists to preserve."""
    global _failures_total, _last_failure_at, _last_failure_action
    with _lock:
        _failures_total = 0
        _last_failure_at = None
        _last_failure_action = None
