"""Report schemas."""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, Field

from app.models.enums import ReportStatus


class ReportRead(BaseModel):
    study_id: uuid.UUID
    status: ReportStatus
    content: str | None
    validated_by: uuid.UUID | None
    validated_at: datetime | None
    version_count: int


class ReportEdit(BaseModel):
    content: str = Field(min_length=1)
