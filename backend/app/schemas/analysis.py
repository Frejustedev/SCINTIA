"""Analysis / score schemas."""

from __future__ import annotations

import uuid
from typing import Any

from pydantic import BaseModel, ConfigDict

from app.models.enums import ScoreType


class ExamScoreRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    score_type: ScoreType
    value: str
    details: dict[str, Any] | None
