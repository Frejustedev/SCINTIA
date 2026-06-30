"""Report and its versioned history (AI draft + human edits + validated)."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models._types import TimestampMixin, pg_enum
from app.models.base import Base
from app.models.enums import ReportStatus, ReportVersionKind


class Report(TimestampMixin, Base):
    __tablename__ = "reports"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    study_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("studies.id", ondelete="CASCADE"), unique=True, nullable=False
    )
    status: Mapped[ReportStatus] = mapped_column(
        pg_enum(ReportStatus, "report_status"), default=ReportStatus.draft, nullable=False
    )
    validated_by: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id"))
    validated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    versions: Mapped[list[ReportVersion]] = relationship(
        back_populates="report", cascade="all, delete-orphan", order_by="ReportVersion.version_no"
    )


class ReportVersion(TimestampMixin, Base):
    """Immutable audit trail of report content. The AI draft is kept alongside edits."""

    __tablename__ = "report_versions"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    report_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("reports.id", ondelete="CASCADE"), nullable=False
    )
    version_no: Mapped[int] = mapped_column(Integer, nullable=False)
    kind: Mapped[ReportVersionKind] = mapped_column(
        pg_enum(ReportVersionKind, "report_version_kind"), nullable=False
    )
    content: Mapped[str] = mapped_column(Text, nullable=False)
    ai_model_version: Mapped[str | None] = mapped_column(String(128))
    author: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id"))  # null if AI

    report: Mapped[Report] = relationship(back_populates="versions")
