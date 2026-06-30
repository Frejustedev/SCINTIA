"""Per-study clinical results: organ measurements, lesions, scores, dosimetry."""

from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models._types import JSONType, pg_enum
from app.models.base import Base
from app.models.enums import DosimetryMethod, ScoreType


class OrganMeasurement(Base):
    __tablename__ = "organ_measurements"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    study_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("studies.id", ondelete="CASCADE"), nullable=False
    )
    organ_name: Mapped[str] = mapped_column(String(255), nullable=False)  # TotalSegmentator name
    snomed_code: Mapped[str | None] = mapped_column(String(64))
    volume_ml: Mapped[Decimal | None] = mapped_column(Numeric)
    mean_intensity: Mapped[Decimal | None] = mapped_column(Numeric)
    activity_mbq: Mapped[Decimal | None] = mapped_column(Numeric)
    concentration_mbq_ml: Mapped[Decimal | None] = mapped_column(Numeric)
    pct_injected_activity: Mapped[Decimal | None] = mapped_column(Numeric)  # %AI
    segmentation_corrected: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)


class Lesion(Base):
    """A focus of uptake, anatomically localized via the segmented CT."""

    __tablename__ = "lesions"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    study_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("studies.id", ondelete="CASCADE"), nullable=False
    )
    anatomical_ref: Mapped[str | None] = mapped_column(String(255))  # e.g. "8th right rib"
    intensity: Mapped[Decimal | None] = mapped_column(Numeric)
    ratio: Mapped[Decimal | None] = mapped_column(Numeric)  # lesion / background
    size_mm: Mapped[Decimal | None] = mapped_column(Numeric)
    is_physiological: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    notes: Mapped[str | None] = mapped_column(Text)


class ExamScore(Base):
    __tablename__ = "exam_scores"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    study_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("studies.id", ondelete="CASCADE"), nullable=False
    )
    score_type: Mapped[ScoreType] = mapped_column(pg_enum(ScoreType, "score_type"), nullable=False)
    value: Mapped[str] = mapped_column(String(64), nullable=False)  # number, category, or "4/4"
    details: Mapped[dict[str, object] | None] = mapped_column(JSONType)


class DosimetryResult(Base):
    """Absorbed dose for an organ/lesion. Always carries its uncertainty (Phase 2)."""

    __tablename__ = "dosimetry_results"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    study_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("studies.id", ondelete="CASCADE"))
    treatment_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("treatments.id", ondelete="CASCADE")
    )
    target: Mapped[str] = mapped_column(String(255), nullable=False)  # organ or lesion
    absorbed_dose_gy: Mapped[Decimal] = mapped_column(Numeric, nullable=False)
    uncertainty_gy: Mapped[Decimal | None] = mapped_column(Numeric)
    tia: Mapped[Decimal | None] = mapped_column(Numeric)  # time-integrated activity
    method: Mapped[DosimetryMethod] = mapped_column(
        pg_enum(DosimetryMethod, "dosimetry_method"), nullable=False
    )
    engine: Mapped[str | None] = mapped_column(String(32))  # mirdcalc / olinda
    model_version: Mapped[str | None] = mapped_column(String(64))


class Treatment(Base):
    """Multi-cycle therapy follow-up (advanced, Phase 2+)."""

    __tablename__ = "treatments"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    patient_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("patients.id"), nullable=False)
    radiopharmaceutical: Mapped[str] = mapped_column(String(255), nullable=False)
    cycle: Mapped[int | None] = mapped_column(Integer)
    administered_activity_mbq: Mapped[Decimal | None] = mapped_column(Numeric)
    administered_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
