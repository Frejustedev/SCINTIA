"""Report endpoints: draft, read, edit, validate, export PDF."""

from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from fastapi.responses import JSONResponse
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.audit import record_audit
from app.core.authz import can_view_study
from app.core.config import get_settings
from app.core.crypto import decrypt_identity
from app.core.db import get_db
from app.core.security import CurrentUser, require_roles
from app.models.clinical import ExamScore, OrganMeasurement
from app.models.enums import ReportStatus, Role
from app.models.patient import PatientIdentity
from app.models.report import Report
from app.models.study import Study
from app.models.user import User
from app.schemas.report import ReportEdit, ReportRead
from app.services.export import build_report_pdf
from app.services.interop import build_dicom_sr, build_fhir_diagnostic_report
from app.services.report import current_content, generate_report, save_edit, validate_report
from app.services.report_generation import EXAM_LABELS, get_report_generator

router = APIRouter(prefix="/studies/{study_id}", tags=["reports"])


def _get_study(db: Session, study_id: uuid.UUID, user: User) -> Study:
    study = db.get(Study, study_id)
    if study is None or not can_view_study(user, study):
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
    study = _get_study(db, study_id, current_user)
    report = generate_report(db, study=study, generator=get_report_generator())
    record_audit(db, action="report.generate", user_id=current_user.id, study_id=study_id)
    return _to_read(study, report)


@router.get("/report", response_model=ReportRead)
def read_report(
    study_id: uuid.UUID,
    db: Annotated[Session, Depends(get_db)],
    current_user: CurrentUser,
) -> ReportRead:
    study = _get_study(db, study_id, current_user)
    return _to_read(study, _get_report(db, study_id))


@router.patch("/report", response_model=ReportRead)
def edit_report(
    study_id: uuid.UUID,
    payload: ReportEdit,
    db: Annotated[Session, Depends(get_db)],
    current_user: CurrentUser,
) -> ReportRead:
    study = _get_study(db, study_id, current_user)
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
    study = _get_study(db, study_id, validator)
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
    """Export the report.

    - ``pdf``: re-identified (decrypts the identity locally; PDF requires validation).
    - ``fhir`` / ``dicom-sr``: pseudonymous structured exports for the RIS/PACS — no
      real identity is ever included.
    """
    study = _get_study(db, study_id, current_user)
    report = _get_report(db, study_id)
    content = current_content(report) or ""
    validated = report.status is ReportStatus.validated
    exam_label = EXAM_LABELS.get(study.exam_type.value, study.exam_type.value)
    pseudonym = study.patient.pseudonym

    if export_format == "fhir":
        score = db.scalar(
            select(ExamScore).where(ExamScore.study_id == study_id).order_by(ExamScore.id.desc())
        )
        organs = list(
            db.scalars(
                select(OrganMeasurement)
                .where(OrganMeasurement.study_id == study_id)
                .order_by(OrganMeasurement.organ_name)
            )
        )
        fhir = build_fhir_diagnostic_report(
            pseudonym=pseudonym,
            exam_label=exam_label,
            content=content,
            validated=validated,
            issued_iso=report.validated_at.isoformat() if report.validated_at is not None else None,
            score_type=score.score_type.value if score is not None else None,
            score_value=score.value if score is not None else None,
            organs=[
                (o.organ_name, float(o.volume_ml) if o.volume_ml is not None else None)
                for o in organs
            ],
        )
        record_audit(db, action="export.fhir", user_id=current_user.id, study_id=study_id)
        return JSONResponse(
            content=fhir,
            headers={"Content-Disposition": f'attachment; filename="CR_{pseudonym}.fhir.json"'},
        )

    if export_format == "dicom-sr":
        sr = build_dicom_sr(
            pseudonym=pseudonym, exam_label=exam_label, content=content, validated=validated
        )
        record_audit(db, action="export.dicom_sr", user_id=current_user.id, study_id=study_id)
        return Response(
            content=sr,
            media_type="application/dicom",
            headers={"Content-Disposition": f'attachment; filename="CR_{pseudonym}.sr.dcm"'},
        )

    if export_format != "pdf":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Format non supporté.")

    # PDF is the re-identified export and requires a validated report.
    if not validated:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Validez le compte-rendu avant l'export.",
        )
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
        exam_label=exam_label,
        identity=identity,
        content=content,
        validated_by_name=validator_name,
        validated_at=report.validated_at.isoformat() if report.validated_at is not None else None,
    )
    record_audit(db, action="export.pdf", user_id=current_user.id, study_id=study_id)
    return Response(
        content=pdf,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="CR_{pseudonym}.pdf"'},
    )
