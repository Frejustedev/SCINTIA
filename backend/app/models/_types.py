"""Shared SQLAlchemy column types and mixins for ORM models.

These keep the models faithful to the Postgres data model (docs/04_MODELE_DONNEES.md)
while remaining usable on SQLite for fast unit tests: PostgreSQL-specific types
degrade gracefully on other backends.
"""

from __future__ import annotations

import enum
from datetime import datetime
from typing import TypeVar

from sqlalchemy import DateTime, String, func
from sqlalchemy import Enum as SAEnum
from sqlalchemy.dialects.postgresql import INET, JSONB
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import JSON, TypeEngine

_E = TypeVar("_E", bound=enum.Enum)

# JSONB on PostgreSQL, generic JSON elsewhere.
JSONType: TypeEngine[object] = JSON().with_variant(JSONB(), "postgresql")
# Native INET on PostgreSQL, an IPv6-sized string elsewhere.
INETType: TypeEngine[str] = String(45).with_variant(INET(), "postgresql")


def pg_enum(enum_cls: type[_E], name: str) -> SAEnum:
    """A native enum that persists member *values* (not names), e.g. ``Tc-99m``."""
    return SAEnum(
        enum_cls,
        name=name,
        native_enum=True,
        values_callable=lambda e: [member.value for member in e],
    )


class TimestampMixin:
    """Adds a server-defaulted ``created_at`` (timestamptz) column."""

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
