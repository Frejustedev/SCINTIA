"""A study (one exam) and its DICOM series."""

from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import Boolean, DateTime, ForeignKey, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models._types import JSONType, TimestampMixin, pg_enum
from app.models.base import Base
from app.models.enums import ExamType, Isotope, SeriesKind, StudyStatus
from app.models.patient import Patient


class Study(TimestampMixin, Base):
    __tablename__ = "studies"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    patient_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("patients.id"), nullable=False)
    exam_type: Mapped[ExamType] = mapped_column(pg_enum(ExamType, "exam_type"), nullable=False)
    status: Mapped[StudyStatus] = mapped_column(
        pg_enum(StudyStatus, "study_status"),
        default=StudyStatus.uploaded,
        nullable=False,
    )
    isotope: Mapped[Isotope | None] = mapped_column(pg_enum(Isotope, "isotope"))
    radiopharmaceutical: Mapped[str | None] = mapped_column(String(255))
    # Net injected activity (syringe minus residual, decay-corrected).
    injected_activity_mbq: Mapped[Decimal | None] = mapped_column(Numeric)
    injection_time: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    acquisition_time: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    device_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("devices.id"))
    error_message: Mapped[str | None] = mapped_column(Text)
    created_by: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id"))

    patient: Mapped[Patient] = relationship()
    series: Mapped[list[StudySeries]] = relationship(
        back_populates="study", cascade="all, delete-orphan"
    )


class StudySeries(Base):
    """A CT or SPECT series belonging to a study (object-storage backed)."""

    __tablename__ = "study_series"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    study_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("studies.id", ondelete="CASCADE"), nullable=False
    )
    kind: Mapped[SeriesKind] = mapped_column(pg_enum(SeriesKind, "series_kind"), nullable=False)
    storage_path: Mapped[str] = mapped_column(String(1024), nullable=False)
    anonymized: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    # Raw DICOM blobs deleted after analysis (data-retention / minimization, docs/05).
    purged: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    # For multi-time-point dosimetry.
    time_point: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    # De-identified, useful DICOM tags only.
    series_metadata: Mapped[dict[str, object] | None] = mapped_column("metadata", JSONType)

    study: Mapped[Study] = relationship(back_populates="series")
