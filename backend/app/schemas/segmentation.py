"""Segmentation schemas."""

from __future__ import annotations

import uuid
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class OrganMeasurementRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    organ_name: str
    snomed_code: str | None
    volume_ml: Decimal | None
    segmentation_corrected: bool


class MeasurementCorrection(BaseModel):
    """Manual correction of a segmentation-derived volume (mandatory capability)."""

    volume_ml: Decimal = Field(gt=0)
