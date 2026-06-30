"""MIBG analyzer (Curie / SIOPEN score) — framework.

Curie and SIOPEN are segmental scoring systems (skeleton + soft tissue) rated by
the physician. This framework reports the factual foci count and flags the score
for clinical scoring; it never fabricates a Curie/SIOPEN value.
"""

from __future__ import annotations

from app.models.clinical import Lesion, OrganMeasurement
from app.models.enums import ExamType, ScoreType
from app.services.exams.base import ExamAnalyzer, ExamResult

_NOTE = (
    "Scores de Curie / SIOPEN : cotation segmentale (squelette + tissus mous) "
    "à réaliser par le médecin. Non calculée automatiquement."
)


class MibgAnalyzer(ExamAnalyzer):
    exam_type = ExamType.mibg
    model_version = "mibg-framework-0"

    def analyze(self, *, organs: list[OrganMeasurement], lesions: list[Lesion]) -> ExamResult:
        foci = [lesion for lesion in lesions if not lesion.is_physiological]
        return ExamResult(
            summary=f"{len(foci)} foyer(s) MIBG-avide(s) recensé(s).",
            score_type=ScoreType.curie,
            score_value="—",
            details={
                "n_foci": len(foci),
                "method": "curie_siopen_segmental",
                "needs_clinical_validation": True,
                "note": _NOTE,
            },
        )
