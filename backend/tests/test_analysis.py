"""Per-exam analysis: bone scan proxy score and the analyzer registry."""

from __future__ import annotations

from decimal import Decimal

import pytest
from sqlalchemy.orm import Session

from app.models import Lesion, OrganMeasurement, Patient, Study
from app.models.enums import ExamType, ScoreType, StudyStatus
from app.services.analysis import run_analysis
from app.services.exams import get_analyzer


def _bone_study_with_findings(db: Session) -> Study:
    patient = Patient(pseudonym="SC-analysis")
    db.add(patient)
    db.flush()
    study = Study(patient_id=patient.id, exam_type=ExamType.bone, status=StudyStatus.quantifying)
    db.add(study)
    db.flush()
    db.add_all(
        [
            OrganMeasurement(study_id=study.id, organ_name="vertebrae_L3", volume_ml=Decimal("40")),
            OrganMeasurement(study_id=study.id, organ_name="sacrum", volume_ml=Decimal("60")),
        ]
    )
    db.add(Lesion(study_id=study.id, anatomical_ref="vertebrae_L3", is_physiological=False))
    db.add(Lesion(study_id=study.id, anatomical_ref="bladder", is_physiological=True))
    db.flush()
    return study


def test_bone_analysis_computes_proxy_and_flags_validation(db_session: Session) -> None:
    study = _bone_study_with_findings(db_session)
    score = run_analysis(db_session, study=study)

    assert score.score_type is ScoreType.bsi
    # involved 40 / total 100 * 100 = 40.0
    assert float(score.value) == 40.0
    assert score.details is not None
    assert score.details["n_foci"] == 1  # physiological focus excluded
    assert score.details["needs_clinical_validation"] is True
    assert study.status is StudyStatus.analyzing


def test_unsupported_exam_has_no_analyzer_yet() -> None:
    with pytest.raises(NotImplementedError):
        get_analyzer(ExamType.octreotide)
