"""Report lifecycle: AI draft -> human edits -> validation.

The « Brouillon généré par IA — à valider par le médecin » banner is enforced on
every stored version and is non-removable (re-added if an edit drops it). Both the
AI draft and the edited versions are kept for audit (docs/04, docs/05).
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.clinical import ExamScore, Lesion, OrganMeasurement
from app.models.enums import ReportStatus, ReportVersionKind, StudyStatus
from app.models.report import Report, ReportVersion
from app.models.study import Study
from app.services.report_generation import (
    FocusCtx,
    OrganVolumeCtx,
    ReportContext,
    ReportGenerator,
)

BANNER = "Brouillon généré par IA — à valider par le médecin."


def ensure_banner(text: str) -> str:
    """Guarantee the non-removable AI banner is present."""
    body = text.strip()
    if BANNER in body:
        return body
    return f"{BANNER}\n\n{body}"


def _next_version_no(report: Report) -> int:
    return max((version.version_no for version in report.versions), default=0) + 1


def current_content(report: Report) -> str | None:
    if not report.versions:
        return None
    return max(report.versions, key=lambda v: v.version_no).content


def build_context(db: Session, study: Study) -> ReportContext:
    organs = list(
        db.scalars(
            select(OrganMeasurement)
            .where(OrganMeasurement.study_id == study.id)
            .order_by(OrganMeasurement.organ_name)
        )
    )
    lesions = list(db.scalars(select(Lesion).where(Lesion.study_id == study.id)))
    score = db.scalar(
        select(ExamScore).where(ExamScore.study_id == study.id).order_by(ExamScore.id.desc())
    )
    return ReportContext(
        exam_type=study.exam_type.value,
        pseudonym=study.patient.pseudonym,
        organs=[
            OrganVolumeCtx(
                organ_name=o.organ_name,
                volume_ml=float(o.volume_ml) if o.volume_ml is not None else None,
                corrected=o.segmentation_corrected,
            )
            for o in organs
        ],
        score_value=score.value if score is not None else None,
        score_type=score.score_type.value if score is not None else None,
        score_details=(score.details or {}) if score is not None else {},
        foci=[
            FocusCtx(
                anatomical_ref=lesion.anatomical_ref,
                ratio=float(lesion.ratio) if lesion.ratio is not None else None,
                size_mm=float(lesion.size_mm) if lesion.size_mm is not None else None,
            )
            for lesion in lesions
            if not lesion.is_physiological
        ],
    )


def generate_report(db: Session, *, study: Study, generator: ReportGenerator) -> Report:
    """Produce an AI draft and store it as version 1 (or a new ai_draft version)."""
    study.status = StudyStatus.generating_report
    db.flush()

    draft = ensure_banner(generator.generate(build_context(db, study)))
    report = db.scalar(select(Report).where(Report.study_id == study.id))
    if report is None:
        report = Report(study_id=study.id, status=ReportStatus.draft)
        db.add(report)
        db.flush()
    report.versions.append(
        ReportVersion(
            version_no=_next_version_no(report),
            kind=ReportVersionKind.ai_draft,
            content=draft,
            ai_model_version=generator.model_version,
        )
    )
    report.status = ReportStatus.draft
    db.flush()

    study.status = StudyStatus.ready
    db.flush()
    return report


def save_edit(db: Session, *, report: Report, content: str, author_id: uuid.UUID) -> ReportVersion:
    if report.status is ReportStatus.validated:
        raise ValueError("Le compte-rendu est validé et verrouillé.")
    version = ReportVersion(
        version_no=_next_version_no(report),
        kind=ReportVersionKind.edited,
        content=ensure_banner(content),
        author=author_id,
    )
    report.versions.append(version)
    report.status = ReportStatus.edited
    db.flush()
    return version


def validate_report(db: Session, *, report: Report, validator_id: uuid.UUID) -> ReportVersion:
    content = current_content(report)
    if content is None:
        raise ValueError("Aucun contenu à valider.")
    version = ReportVersion(
        version_no=_next_version_no(report),
        kind=ReportVersionKind.validated,
        content=ensure_banner(content),
        author=validator_id,
    )
    report.versions.append(version)
    report.status = ReportStatus.validated
    report.validated_by = validator_id
    report.validated_at = datetime.now(timezone.utc)
    db.flush()
    return version
