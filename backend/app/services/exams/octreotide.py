"""Octreotide / SSTR analyzer (Krenning score) — framework.

The validated Krenning score (0–4) is a *visual* scale comparing lesion uptake to
liver and spleen, applied by the physician. This framework extracts the factual
findings (foci, max lesion/background ratio) and flags the score as to be applied
and validated — it never fabricates a Krenning value.
"""

from __future__ import annotations

from app.models.clinical import Lesion, OrganMeasurement
from app.models.enums import ExamType, ScoreType
from app.services.exams.base import ExamAnalyzer, ExamResult

_NOTE = (
    "Échelle de Krenning (0–4) à appliquer visuellement par le médecin "
    "(fixation lésionnelle vs foie/rate). Non calculée automatiquement."
)


class OctreotideAnalyzer(ExamAnalyzer):
    exam_type = ExamType.octreotide
    model_version = "octreotide-framework-0"

    def analyze(self, *, organs: list[OrganMeasurement], lesions: list[Lesion]) -> ExamResult:
        foci = [lesion for lesion in lesions if not lesion.is_physiological]
        ratios = [float(focus.ratio) for focus in foci if focus.ratio is not None]
        return ExamResult(
            summary=f"{len(foci)} foyer(s) SSTR-positif(s) recensé(s).",
            score_type=ScoreType.krenning,
            score_value="—",
            details={
                "n_foci": len(foci),
                "max_lesion_ratio": max(ratios) if ratios else None,
                "method": "krenning_visuel",
                "needs_clinical_validation": True,
                "note": _NOTE,
            },
        )
