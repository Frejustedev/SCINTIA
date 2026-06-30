"""user mfa fields

Revision ID: 1db7e7ee14fc
Revises: 89bc0fb1b73c
Create Date: 2026-06-30 20:52:54.374662
"""

from __future__ import annotations

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "1db7e7ee14fc"
down_revision: str | None = "89bc0fb1b73c"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # server_default false: the column is NOT NULL and the users table holds rows.
    op.add_column(
        "users",
        sa.Column("mfa_enabled", sa.Boolean(), nullable=False, server_default=sa.text("false")),
    )
    op.add_column("users", sa.Column("totp_secret", sa.String(length=64), nullable=True))


def downgrade() -> None:
    op.drop_column("users", "totp_secret")
    op.drop_column("users", "mfa_enabled")
