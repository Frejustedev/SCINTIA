"""Study lifecycle service."""

from __future__ import annotations

import uuid
from collections.abc import Mapping

from sqlalchemy.orm import Session

from app.models.enums import ExamType, StudyStatus
from app.models.study import Study
from app.services.patients import create_pseudonymous_patient


def create_study(
    db: Session,
    *,
    exam_type: ExamType,
    created_by: uuid.UUID | None,
    identity: Mapping[str, str],
    identity_key: str,
    device_id: uuid.UUID | None = None,
) -> Study:
    """Create a pseudonymous patient and a study in the initial ``uploaded`` state."""
    patient = create_pseudonymous_patient(db, identity=identity, identity_key=identity_key)
    study = Study(
        patient_id=patient.id,
        exam_type=exam_type,
        status=StudyStatus.uploaded,
        created_by=created_by,
        device_id=device_id,
    )
    db.add(study)
    db.flush()
    return study
