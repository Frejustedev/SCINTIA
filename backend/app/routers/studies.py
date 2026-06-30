"""Study endpoints (create / list / get).

DICOM upload + ingestion is wired in Phase 1.1; here a study is created with a
pseudonymized patient and starts in the ``uploaded`` state.
"""

from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.audit import record_audit
from app.core.config import get_settings
from app.core.db import get_db
from app.core.security import CurrentUser
from app.models.study import Study
from app.schemas.study import StudyCreate, StudyRead
from app.services.studies import create_study

router = APIRouter(prefix="/studies", tags=["studies"])


def _to_read(study: Study) -> StudyRead:
    return StudyRead(
        id=study.id,
        exam_type=study.exam_type,
        status=study.status,
        patient_pseudonym=study.patient.pseudonym,
        created_at=study.created_at,
    )


@router.post("", response_model=StudyRead, status_code=status.HTTP_201_CREATED)
def create(
    payload: StudyCreate,
    db: Annotated[Session, Depends(get_db)],
    current_user: CurrentUser,
) -> StudyRead:
    identity = payload.patient.to_identity()
    key = get_settings().identity_encryption_key or ""
    if identity and not key:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="IDENTITY_ENCRYPTION_KEY non configurée.",
        )
    study = create_study(
        db,
        exam_type=payload.exam_type,
        created_by=current_user.id,
        identity=identity,
        identity_key=key,
        device_id=payload.device_id,
    )
    record_audit(
        db,
        action="study.create",
        user_id=current_user.id,
        study_id=study.id,
        details={"exam_type": payload.exam_type.value},
    )
    return _to_read(study)


@router.get("", response_model=list[StudyRead])
def list_studies(
    db: Annotated[Session, Depends(get_db)],
    current_user: CurrentUser,
    limit: Annotated[int, Query(ge=1, le=200)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> list[StudyRead]:
    studies = db.scalars(
        select(Study).order_by(Study.created_at.desc()).limit(limit).offset(offset)
    )
    return [_to_read(s) for s in studies]


@router.get("/{study_id}", response_model=StudyRead)
def get_study(
    study_id: uuid.UUID,
    db: Annotated[Session, Depends(get_db)],
    current_user: CurrentUser,
) -> StudyRead:
    study = db.get(Study, study_id)
    if study is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Examen introuvable.")
    return _to_read(study)
