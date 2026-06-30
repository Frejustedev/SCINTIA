"""Longitudinal follow-up: a patient's prior exams of the same type.

Studies of one patient share the pseudonymous ``patient_id``. This service returns
the earlier exams (same exam type), each with its latest score, so the report can
state the trend factually and a follow-up view can compare across time.
"""

from __future__ import annotations

import dataclasses
import uuid
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.authz import study_visibility_clause
from app.models.clinical import ExamScore
from app.models.study import Study
from app.models.user import User


@dataclasses.dataclass(frozen=True)
class PriorStudy:
    study_id: uuid.UUID
    exam_type: str
    status: str
    created_at: datetime
    score_type: str | None
    score_value: str | None


def prior_studies(db: Session, *, study: Study, viewer: User | None = None) -> list[PriorStudy]:
    """Earlier studies of the same patient and exam type, chronological (oldest first).

    When ``viewer`` is given, the list is further restricted to studies that viewer
    is allowed to see (RBAC scoping). Omit ``viewer`` for server-side report drafting.
    """
    stmt = (
        select(Study).where(
            Study.patient_id == study.patient_id,
            Study.exam_type == study.exam_type,
            Study.id != study.id,
            Study.created_at < study.created_at,  # strictly earlier (matches the contract)
        )
        # Secondary key keeps ordering deterministic if timestamps ever tie.
        .order_by(Study.created_at.asc(), Study.id.asc())
    )
    if viewer is not None:
        stmt = stmt.where(study_visibility_clause(viewer))

    priors: list[PriorStudy] = []
    for prior in db.scalars(stmt):
        score = db.scalar(
            select(ExamScore).where(ExamScore.study_id == prior.id).order_by(ExamScore.id.desc())
        )
        priors.append(
            PriorStudy(
                study_id=prior.id,
                exam_type=prior.exam_type.value,
                status=prior.status.value,
                created_at=prior.created_at,
                score_type=score.score_type.value if score is not None else None,
                score_value=score.value if score is not None else None,
            )
        )
    return priors
