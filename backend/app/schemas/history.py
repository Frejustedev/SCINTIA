"""Schemas for the longitudinal follow-up endpoint."""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class StudyHistoryEntry(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    study_id: uuid.UUID
    exam_type: str
    status: str
    created_at: datetime
    score_type: str | None
    score_value: str | None
