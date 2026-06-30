"""Parathyroid analyzer (adenoma localization) — framework.

The output is an anatomical localization, not a numeric score (hence no
score_type). Localization on dual-phase + SPECT/CT is performed by the physician;
this framework records the exam and flags it for that read.
"""

from __future__ import annotations

from app.models.clinical import Lesion, OrganMeasurement
from app.models.enums import ExamType
from app.services.exams.base import ExamAnalyzer, ExamResult

_NOTE = (
    "Localisation d'un adénome parathyroïdien : double phase + SPECT/CT, "
    "interprétation et localisation anatomique par le médecin."
)


class ParathyroidAnalyzer(ExamAnalyzer):
    exam_type = ExamType.parathyroid
    model_version = "parathyroid-framework-0"

    def analyze(self, *, organs: list[OrganMeasurement], lesions: list[Lesion]) -> ExamResult:
        return ExamResult(
            summary="Localisation d'adénome parathyroïdien à préciser par le médecin.",
            details={
                "method": "dual_phase_spect_ct",
                "needs_clinical_validation": True,
                "note": _NOTE,
            },
        )
