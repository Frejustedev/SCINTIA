"""Myocardial SPECT analyzer (LVEF, SSS/SRS/SDS) — framework.

LVEF, the 17-segment model and the SSS/SRS/SDS scores require a gated acquisition
and polar maps (a dedicated cardiac pipeline). This framework records the exam and
flags those outputs as to be computed/validated by the physician.
"""

from __future__ import annotations

from app.models.clinical import Lesion, OrganMeasurement
from app.models.enums import ExamType, ScoreType
from app.services.exams.base import ExamAnalyzer, ExamResult

_NOTE = (
    "FEVG, modèle 17 segments et scores SSS/SRS/SDS requièrent une acquisition "
    "synchronisée (gated) et des cartes polaires (pipeline cardiaque dédié). "
    "À calculer et valider par le médecin."
)


class MyocardialSpectAnalyzer(ExamAnalyzer):
    exam_type = ExamType.myocardial_spect
    model_version = "myocardial-framework-0"

    def analyze(self, *, organs: list[OrganMeasurement], lesions: list[Lesion]) -> ExamResult:
        return ExamResult(
            summary="SPECT myocardique — analyse fonctionnelle (gated) requise.",
            score_type=ScoreType.lvef,
            score_value="—",
            details={
                "method": "gated_spect_polar_map",
                "needs_clinical_validation": True,
                "note": _NOTE,
            },
        )
