"""Make audit_logs.request_id FK DEFERRABLE INITIALLY DEFERRED (B3)

The submit route writes two request_id-bearing audit rows (intent.declared,
authorization_submitted) BEFORE the parent authorization_requests row, because
intent.declared must be the first audit event (the pre-write-audit invariant) and
audit writes flush immediately. A non-deferrable FK is checked at statement time,
so on Postgres that first flush raises ForeignKeyViolationError before the parent
exists. Deferring the check to COMMIT (one commit per request) satisfies the FK
once the parent row — flushed mid-transaction — is present, without reordering
the audit writes.

Postgres-only: deferrable constraints are a Postgres feature, and SQLite does not
enforce FKs at all. Dev/test builds the schema from the models via create_all,
which already emits the deferrable clause (SQLite ignores it), so this migration
no-ops off Postgres.

Revision ID: 003_deferrable_audit_fk
Revises: 002_nullable_request_fields
Create Date: 2026-07-23

"""

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "003_deferrable_audit_fk"
down_revision: str | None = "002_nullable_request_fields"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

# Postgres auto-generates this name for the unnamed FK created in migration 001.
_FK = "audit_logs_request_id_fkey"


def upgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name != "postgresql":
        return
    op.drop_constraint(_FK, "audit_logs", type_="foreignkey")
    op.create_foreign_key(
        _FK,
        "audit_logs",
        "authorization_requests",
        ["request_id"],
        ["request_id"],
        deferrable=True,
        initially="DEFERRED",
    )


def downgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name != "postgresql":
        return
    op.drop_constraint(_FK, "audit_logs", type_="foreignkey")
    op.create_foreign_key(
        _FK,
        "audit_logs",
        "authorization_requests",
        ["request_id"],
        ["request_id"],
    )
