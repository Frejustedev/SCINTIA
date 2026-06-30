"""Ingestion schemas."""

from __future__ import annotations

import uuid

from pydantic import BaseModel

from app.models.enums import StudyStatus


class IngestionSummary(BaseModel):
    """Result of a DICOM upload + de-identification + CT/SPECT separation."""

    study_id: uuid.UUID
    status: StudyStatus
    ct_series: int
    spect_series: int
    instances: int
    skipped: int
