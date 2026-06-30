"""User accounts (authentication + RBAC)."""

from __future__ import annotations

import uuid

from sqlalchemy import Boolean, String
from sqlalchemy.orm import Mapped, mapped_column

from app.models._types import TimestampMixin, pg_enum
from app.models.base import Base
from app.models.enums import Role


class User(TimestampMixin, Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    # Never stored in clear (argon2/bcrypt) — docs/05_CONTRAINTES_SECURITE.md.
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[Role] = mapped_column(pg_enum(Role, "role"), nullable=False)
    # Optional TOTP MFA (app.core.mfa). The secret is only used to verify codes.
    mfa_enabled: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    totp_secret: Mapped[str | None] = mapped_column(String(64))
