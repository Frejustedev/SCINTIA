"""rbac scoping retention

Revision ID: e4ce5b593e78
Revises: 1576a61b6fbe
Create Date: 2026-06-30 20:31:27.109606
"""

from __future__ import annotations

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "e4ce5b593e78"
down_revision: str | None = "1576a61b6fbe"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.drop_constraint(op.f("audit_log_study_id_fkey"), "audit_log", type_="foreignkey")
    op.create_foreign_key(
        "audit_log_study_id_fkey",
        "audit_log",
        "studies",
        ["study_id"],
        ["id"],
        ondelete="SET NULL",
    )
    # server_default false: the column is NOT NULL and the table may already hold rows.
    op.add_column(
        "study_series",
        sa.Column("purged", sa.Boolean(), nullable=False, server_default=sa.text("false")),
    )


def downgrade() -> None:
    op.drop_column("study_series", "purged")
    op.drop_constraint("audit_log_study_id_fkey", "audit_log", type_="foreignkey")
    op.create_foreign_key("audit_log_study_id_fkey", "audit_log", "studies", ["study_id"], ["id"])
