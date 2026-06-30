"""Study schemas.

The patient identity supplied at creation is encrypted server-side and never
leaves; the API works with the pseudonym thereafter.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import ExamType, StudyStatus


class PatientIdentityIn(BaseModel):
    """Real identity provided at study creation (encrypted at rest, never sent out)."""

    name: str | None = Field(default=None, max_length=255)
    birth_date: str | None = Field(default=None, max_length=32)
    patient_id: str | None = Field(default=None, max_length=128)

    def to_identity(self) -> dict[str, str]:
        identity: dict[str, str] = {}
        if self.name:
            identity["PatientName"] = self.name
        if self.patient_id:
            identity["PatientID"] = self.patient_id
        if self.birth_date:
            identity["PatientBirthDate"] = self.birth_date
        return identity


class StudyCreate(BaseModel):
    exam_type: ExamType
    patient: PatientIdentityIn = PatientIdentityIn()
    device_id: uuid.UUID | None = None


class StudyRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    exam_type: ExamType
    status: StudyStatus
    patient_pseudonym: str
    created_at: datetime
