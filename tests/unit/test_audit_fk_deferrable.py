"""
Deferrable audit FK — PRODUCTION_READINESS B3.

The submit route flushes two ``request_id``-bearing audit rows
(``intent.declared``, ``authorization_submitted``) BEFORE the parent
``authorization_requests`` row is created — because ``intent.declared`` must be
the first audit event (the pre-write-audit safety invariant), and audit writes
flush immediately. On Postgres a non-deferrable FK is checked at statement time,
so that first flush raises ``ForeignKeyViolationError: audit_logs_request_id_fkey``
before the parent exists. SQLite doesn't enforce FKs, which is why the unit suite
never caught it.

The fix keeps both invariants: make ``audit_logs.request_id`` FK
``DEFERRABLE INITIALLY DEFERRED`` so it is checked at COMMIT (a single commit per
request), by which point the parent row — flushed mid-transaction — exists.

This test compiles the DDL under the Postgres dialect, so it verifies the
constraint's deferral WITHOUT a live Postgres (the SQLite suite structurally
cannot). A live-Postgres reproduction is done separately at implementation time.
"""

from __future__ import annotations

from sqlalchemy.dialects import postgresql
from sqlalchemy.schema import CreateTable

from pacca.db.models import AuditLogModel


def _audit_ddl_postgres() -> str:
    return str(CreateTable(AuditLogModel.__table__).compile(dialect=postgresql.dialect()))


def test_audit_request_id_fk_is_deferrable_initially_deferred() -> None:
    ddl = _audit_ddl_postgres()
    # audit_logs has exactly one FK (request_id → authorization_requests);
    # decision_id carries no FK. So this clause can only be that FK.
    assert "REFERENCES authorization_requests" in ddl, "the request_id FK vanished"
    assert "DEFERRABLE INITIALLY DEFERRED" in ddl, (
        "audit_logs.request_id FK is not DEFERRABLE INITIALLY DEFERRED — on "
        "Postgres it will be checked at statement time and reject the pre-flight "
        "audit writes before the parent row exists (B3)"
    )


def test_the_deferral_is_on_the_request_id_fk() -> None:
    """Pin the deferral to the request_id FK specifically, not some other clause."""
    ddl = _audit_ddl_postgres()
    fk_lines = [line for line in ddl.splitlines() if "FOREIGN KEY" in line and "request_id" in line]
    assert fk_lines, "no request_id FOREIGN KEY clause found in the compiled DDL"
    assert all("DEFERRABLE INITIALLY DEFERRED" in line for line in fk_lines)
