"""Lung V/P analyzer (PIOPED probability) — framework.

The PIOPED probability (normal / low / intermediate / high) comes from analyzing
ventilation/perfusion mismatches, read by the physician. This framework records
the exam and flags the category for clinical interpretation.
"""

from __future__ import annotations

from app.models.clinical import Lesion, OrganMeasurement
from app.models.enums import ExamType, ScoreType
from app.services.exams.base import ExamAnalyzer, ExamResult

_NOTE = (
    "Probabilité PIOPED (normale / faible / intermédiaire / haute) : analyse des "
    "discordances ventilation/perfusion à interpréter par le médecin."
)


class LungVQAnalyzer(ExamAnalyzer):
    exam_type = ExamType.lung_vq
    model_version = "lung-vq-framework-0"

    def analyze(self, *, organs: list[OrganMeasurement], lesions: list[Lesion]) -> ExamResult:
        return ExamResult(
            summary="Scintigraphie V/P — discordances à interpréter (PIOPED).",
            score_type=ScoreType.pioped,
            score_value="—",
            details={
                "method": "pioped_vq_mismatch",
                "needs_clinical_validation": True,
                "note": _NOTE,
            },
        )
