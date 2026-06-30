"""Append-only audit log (docs/05_CONTRAINTES_SECURITE.md).

Never updated or deleted: every sensitive action (upload, segmentation
correction, report validation, export, identity access) is recorded here.
"""

from __future__ import annotations

import uuid

from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from app.models._types import INETType, JSONType, TimestampMixin
from app.models.base import Base


class AuditLog(TimestampMixin, Base):
    __tablename__ = "audit_log"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id"))
    # SET NULL (not CASCADE): the append-only log survives a study's erasure; only
    # the link to the now-deleted study is cleared (right-to-erasure, docs/05).
    study_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("studies.id", ondelete="SET NULL")
    )
    action: Mapped[str] = mapped_column(String(128), nullable=False)  # e.g. study.upload
    details: Mapped[dict[str, object] | None] = mapped_column(JSONType)
    ip: Mapped[str | None] = mapped_column(INETType)
