"""Report endpoints: draft, read, edit, validate, export PDF."""

from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.audit import record_audit
from app.core.config import get_settings
from app.core.crypto import decrypt_identity
from app.core.db import get_db
from app.core.security import CurrentUser, require_roles
from app.models.enums import ReportStatus, Role
from app.models.patient import PatientIdentity
from app.models.report import Report
from app.models.study import Study
from app.models.user import User
from app.schemas.report import ReportEdit, ReportRead
from app.services.export import build_report_pdf
from app.services.report import current_content, generate_report, save_edit, validate_report
from app.services.report_generation import EXAM_LABELS, get_report_generator

router = APIRouter(prefix="/studies/{study_id}", tags=["reports"])


def _get_study(db: Session, study_id: uuid.UUID) -> Study:
    study = db.get(Study, study_id)
    if study is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Examen introuvable.")
    return study


def _get_report(db: Session, study_id: uuid.UUID) -> Report:
    report = db.scalar(select(Report).where(Report.study_id == study_id))
    if report is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Compte-rendu introuvable."
        )
    return report


def _to_read(study: Study, report: Report) -> ReportRead:
    return ReportRead(
        study_id=study.id,
        status=report.status,
        content=current_content(report),
        validated_by=report.validated_by,
        validated_at=report.validated_at,
        version_count=len(report.versions),
    )


@router.post("/report", response_model=ReportRead, status_code=status.HTTP_201_CREATED)
def create_report(
    study_id: uuid.UUID,
    db: Annotated[Session, Depends(get_db)],
    current_user: CurrentUser,
) -> ReportRead:
    study = _get_study(db, study_id)
    report = generate_report(db, study=study, generator=get_report_generator())
    record_audit(db, action="report.generate", user_id=current_user.id, study_id=study_id)
    return _to_read(study, report)


@router.get("/report", response_model=ReportRead)
def read_report(
    study_id: uuid.UUID,
    db: Annotated[Session, Depends(get_db)],
    current_user: CurrentUser,
) -> ReportRead:
    study = _get_study(db, study_id)
    return _to_read(study, _get_report(db, study_id))


@router.patch("/report", response_model=ReportRead)
def edit_report(
    study_id: uuid.UUID,
    payload: ReportEdit,
    db: Annotated[Session, Depends(get_db)],
    current_user: CurrentUser,
) -> ReportRead:
    study = _get_study(db, study_id)
    report = _get_report(db, study_id)
    try:
        save_edit(db, report=report, content=payload.content, author_id=current_user.id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    record_audit(db, action="report.edit", user_id=current_user.id, study_id=study_id)
    return _to_read(study, report)


@router.post("/report/validate", response_model=ReportRead)
def validate(
    study_id: uuid.UUID,
    db: Annotated[Session, Depends(get_db)],
    validator: Annotated[User, require_roles(Role.medecin)],
) -> ReportRead:
    study = _get_study(db, study_id)
    report = _get_report(db, study_id)
    try:
        validate_report(db, report=report, validator_id=validator.id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    record_audit(db, action="report.validate", user_id=validator.id, study_id=study_id)
    return _to_read(study, report)


@router.get("/export")
def export_report(
    study_id: uuid.UUID,
    db: Annotated[Session, Depends(get_db)],
    current_user: CurrentUser,
    export_format: Annotated[str, Query(alias="format")] = "pdf",
) -> Response:
    study = _get_study(db, study_id)
    report = _get_report(db, study_id)
    if report.status is not ReportStatus.validated:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Validez le compte-rendu avant l'export.",
        )
    if export_format != "pdf":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Format non supporté.")

    identity: dict[str, str] = {}
    patient_identity = db.scalar(
        select(PatientIdentity).where(PatientIdentity.patient_id == study.patient_id)
    )
    if patient_identity is not None:
        key = get_settings().identity_encryption_key or ""
        if key:
            identity = decrypt_identity(patient_identity.identity_encrypted, key)
            record_audit(db, action="identity.access", user_id=current_user.id, study_id=study_id)

    validator_name: str | None = None
    if report.validated_by is not None:
        validator = db.get(User, report.validated_by)
        validator_name = validator.full_name if validator is not None else None

    pdf = build_report_pdf(
        exam_label=EXAM_LABELS.get(study.exam_type.value, study.exam_type.value),
        identity=identity,
        content=current_content(report) or "",
        validated_by_name=validator_name,
        validated_at=report.validated_at.isoformat() if report.validated_at is not None else None,
    )
    record_audit(db, action="export.pdf", user_id=current_user.id, study_id=study_id)
    return Response(
        content=pdf,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="CR_{study.patient.pseudonym}.pdf"'},
    )
