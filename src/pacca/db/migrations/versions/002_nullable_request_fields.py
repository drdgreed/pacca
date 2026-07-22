"""Make API-uncollected authorization_request columns nullable (P-4 persistence repair)

The minimal submission API (AuthorizationRequest + its ClinicalCase) does not
collect gender, the diagnosis/treatment descriptions, treatment category, the
provider name, or the payer/member fields. The persistence repair stores honest
NULL for these rather than fabricating audit data, so their columns move from
NOT NULL to nullable. Dev/test builds the schema from the models via create_all;
this migration carries the same change to migration-managed (production) DBs.

Revision ID: 002_nullable_request_fields
Revises: 001_initial
Create Date: 2026-07-22

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "002_nullable_request_fields"
down_revision: str | None = "001_initial"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

# (column, existing type) for the nine fields the minimal API does not collect.
_COLUMNS: list[tuple[str, sa.types.TypeEngine]] = [
    ("patient_age", sa.Integer()),
    ("patient_gender", sa.String(10)),
    ("primary_diagnosis_description", sa.Text()),
    ("treatment_description", sa.Text()),
    ("treatment_category", sa.String(30)),
    ("provider_name", sa.String(200)),
    ("payer_id", sa.String(50)),
    ("payer_name", sa.String(200)),
    ("member_id", sa.String(50)),
]


def upgrade() -> None:
    # batch_alter_table so this works on SQLite (no native ALTER COLUMN) as well
    # as PostgreSQL.
    with op.batch_alter_table("authorization_requests") as batch_op:
        for name, col_type in _COLUMNS:
            batch_op.alter_column(name, existing_type=col_type, nullable=True)


def downgrade() -> None:
    # Reinstates NOT NULL. Requires no NULL rows in these columns (standard
    # downgrade precondition).
    with op.batch_alter_table("authorization_requests") as batch_op:
        for name, col_type in _COLUMNS:
            batch_op.alter_column(name, existing_type=col_type, nullable=False)
