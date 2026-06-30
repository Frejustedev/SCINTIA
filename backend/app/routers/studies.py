"""Study endpoints (create / list / get).

DICOM upload + ingestion is wired in Phase 1.1; here a study is created with a
pseudonymized patient and starts in the ``uploaded`` state.
"""

from __future__ import annotations

import asyncio
import uuid
from typing import Annotated

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Query,
    Response,
    UploadFile,
    WebSocket,
    WebSocketDisconnect,
    status,
)
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.audit import record_audit
from app.core.authz import can_view_study, study_visibility_clause
from app.core.config import get_settings
from app.core.db import get_db
from app.core.security import CurrentUser, decode_token
from app.models.clinical import ExamScore, OrganMeasurement
from app.models.enums import Role, SeriesKind, StudyStatus
from app.models.report import Report
from app.models.study import Study
from app.models.user import User
from app.schemas.analysis import ExamScoreRead
from app.schemas.history import StudyHistoryEntry
from app.schemas.ingestion import IngestionSummary
from app.schemas.results import StudyResults
from app.schemas.segmentation import MeasurementCorrection, OrganMeasurementRead
from app.schemas.study import StudyCreate, StudyRead
from app.services.erasure import erase_study
from app.services.history import prior_studies
from app.services.ingestion import ingest_study
from app.services.pipeline import run_pipeline
from app.services.report_generation import get_report_generator
from app.services.segmentation import get_segmenter
from app.services.storage import ObjectStorage, get_storage
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


def _get_visible_study(db: Session, study_id: uuid.UUID, user: User) -> Study:
    """Fetch a study the user is allowed to see, else 404 (no existence disclosure)."""
    study = db.get(Study, study_id)
    if study is None or not can_view_study(user, study):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Examen introuvable.")
    return study


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
        select(Study)
        .where(study_visibility_clause(current_user))
        .order_by(Study.created_at.desc())
        .limit(limit)
        .offset(offset)
    )
    return [_to_read(s) for s in studies]


@router.get("/{study_id}", response_model=StudyRead)
def get_study(
    study_id: uuid.UUID,
    db: Annotated[Session, Depends(get_db)],
    current_user: CurrentUser,
) -> StudyRead:
    return _to_read(_get_visible_study(db, study_id, current_user))


@router.post("/{study_id}/files", response_model=IngestionSummary)
async def upload_files(
    study_id: uuid.UUID,
    files: list[UploadFile],
    db: Annotated[Session, Depends(get_db)],
    current_user: CurrentUser,
    storage: Annotated[ObjectStorage, Depends(get_storage)],
) -> IngestionSummary:
    """Upload DICOM files: they are de-identified and separated CT/SPECT, then stored."""
    study = _get_visible_study(db, study_id, current_user)
    blobs = [await file.read() for file in files]
    key = get_settings().identity_encryption_key or ""
    result = ingest_study(db, storage, study=study, blobs=blobs, identity_key=key)
    record_audit(
        db,
        action="study.upload",
        user_id=current_user.id,
        study_id=study.id,
        details={
            "ct_series": result.ct_series,
            "spect_series": result.spect_series,
            "instances": result.instances,
            "skipped": result.skipped,
        },
    )
    return IngestionSummary(
        study_id=study.id,
        status=study.status,
        ct_series=result.ct_series,
        spect_series=result.spect_series,
        instances=result.instances,
        skipped=result.skipped,
    )


@router.get("/{study_id}/segmentation", response_model=list[OrganMeasurementRead])
def list_segmentation(
    study_id: uuid.UUID,
    db: Annotated[Session, Depends(get_db)],
    current_user: CurrentUser,
) -> list[OrganMeasurement]:
    _get_visible_study(db, study_id, current_user)
    return list(
        db.scalars(
            select(OrganMeasurement)
            .where(OrganMeasurement.study_id == study_id)
            .order_by(OrganMeasurement.organ_name)
        )
    )


@router.patch("/{study_id}/measurements/{measurement_id}", response_model=OrganMeasurementRead)
def correct_measurement(
    study_id: uuid.UUID,
    measurement_id: uuid.UUID,
    payload: MeasurementCorrection,
    db: Annotated[Session, Depends(get_db)],
    current_user: CurrentUser,
) -> OrganMeasurement:
    """Manually correct a segmentation-derived volume (mandatory clinical capability)."""
    _get_visible_study(db, study_id, current_user)
    measurement = db.get(OrganMeasurement, measurement_id)
    if measurement is None or measurement.study_id != study_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Mesure introuvable.")
    measurement.volume_ml = payload.volume_ml
    measurement.segmentation_corrected = True
    db.flush()
    record_audit(
        db,
        action="segmentation.correct",
        user_id=current_user.id,
        study_id=study_id,
        details={"measurement_id": str(measurement_id)},
    )
    return measurement


@router.get("/{study_id}/score", response_model=ExamScoreRead | None)
def get_score(
    study_id: uuid.UUID,
    db: Annotated[Session, Depends(get_db)],
    current_user: CurrentUser,
) -> ExamScore | None:
    _get_visible_study(db, study_id, current_user)
    return db.scalar(
        select(ExamScore).where(ExamScore.study_id == study_id).order_by(ExamScore.id.desc())
    )


@router.post("/{study_id}/analyze", response_model=StudyRead)
def analyze(
    study_id: uuid.UUID,
    db: Annotated[Session, Depends(get_db)],
    current_user: CurrentUser,
    storage: Annotated[ObjectStorage, Depends(get_storage)],
) -> StudyRead:
    """Run the analysis pipeline (segment -> quantify -> analyze -> report).

    Synchronous in Phase 1; on a deployed stack this enqueues a Celery task
    (app.workers.tasks.run_pipeline_task) so GPU work runs off the request.
    """
    study = _get_visible_study(db, study_id, current_user)
    if not any(series.kind is SeriesKind.ct for series in study.series):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Aucune série CT — chargez d'abord les fichiers DICOM.",
        )

    # Production path: enqueue the pipeline on Celery so GPU work runs off-request.
    if get_settings().celery_broker_url:
        from app.workers.tasks import run_pipeline_task

        run_pipeline_task.delay(str(study_id))
        record_audit(
            db, action="study.analyze.enqueued", user_id=current_user.id, study_id=study_id
        )
        return _to_read(study)

    # Offline / no broker: run synchronously.
    try:
        run_pipeline(
            db,
            storage,
            study=study,
            segmenter=get_segmenter(),
            generator=get_report_generator(),
        )
        record_audit(db, action="study.analyze", user_id=current_user.id, study_id=study_id)
    except Exception:  # failure is persisted on the study (status=error); detail is logged
        record_audit(db, action="study.error", user_id=current_user.id, study_id=study_id)
    return _to_read(study)


@router.get("/{study_id}/results", response_model=StudyResults)
def get_results(
    study_id: uuid.UUID,
    db: Annotated[Session, Depends(get_db)],
    current_user: CurrentUser,
) -> StudyResults:
    study = _get_visible_study(db, study_id, current_user)
    organs = list(
        db.scalars(
            select(OrganMeasurement)
            .where(OrganMeasurement.study_id == study_id)
            .order_by(OrganMeasurement.organ_name)
        )
    )
    score = db.scalar(
        select(ExamScore).where(ExamScore.study_id == study_id).order_by(ExamScore.id.desc())
    )
    report = db.scalar(select(Report).where(Report.study_id == study_id))
    return StudyResults(
        study=_to_read(study),
        organs=[OrganMeasurementRead.model_validate(o) for o in organs],
        score=ExamScoreRead.model_validate(score) if score is not None else None,
        report_status=report.status if report is not None else None,
    )


@router.get("/{study_id}/history", response_model=list[StudyHistoryEntry])
def study_history(
    study_id: uuid.UUID,
    db: Annotated[Session, Depends(get_db)],
    current_user: CurrentUser,
) -> list[StudyHistoryEntry]:
    """Prior exams of the same patient and exam type (longitudinal follow-up)."""
    study = _get_visible_study(db, study_id, current_user)
    priors = prior_studies(db, study=study, viewer=current_user)
    return [StudyHistoryEntry.model_validate(prior) for prior in priors]


@router.delete("/{study_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_study(
    study_id: uuid.UUID,
    db: Annotated[Session, Depends(get_db)],
    current_user: CurrentUser,
    storage: Annotated[ObjectStorage, Depends(get_storage)],
) -> Response:
    """Right-to-erasure (RGPD / loi 18-07): irreversibly delete a study and, if the
    patient is left with no other study, the encrypted identity. Admin / médecin only.
    """
    if current_user.role not in (Role.admin, Role.medecin):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Accès refusé pour ce rôle."
        )
    study = _get_visible_study(db, study_id, current_user)
    erase_study(db, storage, study=study, actor_id=current_user.id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


_TERMINAL_STATUSES = {StudyStatus.ready, StudyStatus.error}


@router.websocket("/{study_id}/progress")
async def progress(
    websocket: WebSocket,
    study_id: uuid.UUID,
    db: Annotated[Session, Depends(get_db)],
    token: str | None = None,
) -> None:
    """Stream the study status until it reaches a terminal state.

    The JWT is passed as a query param (browsers cannot set WebSocket headers).
    With the Celery execution path this reflects real-time pipeline progress; with
    the synchronous path it emits the final status immediately.
    """
    await websocket.accept()
    try:
        payload = decode_token(token or "")
        user_id = uuid.UUID(str(payload.get("sub")))
    except Exception:
        await websocket.close(code=1008)
        return
    user = db.get(User, user_id)
    if user is None:
        await websocket.close(code=1008)
        return
    initial = db.get(Study, study_id)
    if initial is None or not can_view_study(user, initial):
        await websocket.send_json({"status": "not_found", "error": None})
        await websocket.close()
        return

    try:
        for _ in range(240):
            db.expire_all()
            study = db.get(Study, study_id)
            if study is None:
                await websocket.send_json({"status": "not_found", "error": None})
                break
            await websocket.send_json({"status": study.status.value, "error": study.error_message})
            if study.status in _TERMINAL_STATUSES:
                break
            await asyncio.sleep(0.5)
        await websocket.close()
    except WebSocketDisconnect:
        # Client navigated away — a normal end of stream, not an error.
        return
