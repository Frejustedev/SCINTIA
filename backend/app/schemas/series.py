"""Schemas for DICOM series listing (viewer)."""

from __future__ import annotations

import uuid

from pydantic import BaseModel

from app.models.enums import SeriesKind


class StudySeriesRead(BaseModel):
    id: uuid.UUID
    kind: SeriesKind
    instances: int
    anonymized: bool
    purged: bool
