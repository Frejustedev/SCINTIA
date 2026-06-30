"""Per-exam analysis: bone scan proxy score and the analyzer registry."""

from __future__ import annotations

from decimal import Decimal

from sqlalchemy.orm import Session

from app.models import Lesion, OrganMeasurement, Patient, Study
from app.models.enums import ExamType, ScoreType, StudyStatus
from app.services.analysis import run_analysis
from app.services.exams import get_analyzer
from app.services.exams.parathyroid import ParathyroidAnalyzer


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


def test_all_exam_types_have_an_analyzer() -> None:
    for exam_type in ExamType:
        assert get_analyzer(exam_type).exam_type is exam_type


def test_framework_analyzers_flag_clinical_validation() -> None:
    for exam_type in (
        ExamType.octreotide,
        ExamType.mibg,
        ExamType.myocardial_spect,
        ExamType.lung_vq,
    ):
        result = get_analyzer(exam_type).analyze(organs=[], lesions=[])
        assert result.score_type is not None
        assert result.details["needs_clinical_validation"] is True


def test_parathyroid_yields_localization_without_score() -> None:
    result = ParathyroidAnalyzer().analyze(organs=[], lesions=[])
    assert result.score_type is None
    assert result.score_value is None
    assert result.details["needs_clinical_validation"] is True
