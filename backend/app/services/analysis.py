"""Run the per-exam analyzer (strategy) and persist the standardized score."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.clinical import ExamScore, Lesion, OrganMeasurement
from app.models.enums import StudyStatus
from app.models.study import Study
from app.services.exams import get_analyzer


def run_analysis(db: Session, *, study: Study) -> ExamScore:
    """Apply the exam-specific analyzer and store its score."""
    study.status = StudyStatus.analyzing
    db.flush()

    organs = list(db.scalars(select(OrganMeasurement).where(OrganMeasurement.study_id == study.id)))
    lesions = list(db.scalars(select(Lesion).where(Lesion.study_id == study.id)))

    result = get_analyzer(study.exam_type).analyze(organs=organs, lesions=lesions)
    score = ExamScore(
        study_id=study.id,
        score_type=result.score_type,
        value=result.score_value,
        details=result.details,
    )
    db.add(score)
    db.flush()
    return score
