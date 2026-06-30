"""Gamma cameras and their calibration factors."""

from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, ForeignKey, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from app.models._types import pg_enum
from app.models.base import Base
from app.models.enums import Isotope


class Device(Base):
    __tablename__ = "devices"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    model: Mapped[str | None] = mapped_column(String(255))
    site: Mapped[str | None] = mapped_column(String(255))


class CalibrationFactor(Base):
    """Camera sensitivity (counts/s per MBq) for a given isotope."""

    __tablename__ = "calibration_factors"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    device_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("devices.id"), nullable=False)
    isotope: Mapped[Isotope] = mapped_column(pg_enum(Isotope, "isotope"), nullable=False)
    value: Mapped[Decimal] = mapped_column(Numeric, nullable=False)
    unit: Mapped[str] = mapped_column(String(32), nullable=False)
    calibrated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
