"""Aggregated study results."""

from __future__ import annotations

from pydantic import BaseModel

from app.models.enums import ReportStatus
from app.schemas.analysis import ExamScoreRead
from app.schemas.segmentation import OrganMeasurementRead
from app.schemas.study import StudyRead


class StudyResults(BaseModel):
    study: StudyRead
    organs: list[OrganMeasurementRead]
    score: ExamScoreRead | None
    report_status: ReportStatus | None
