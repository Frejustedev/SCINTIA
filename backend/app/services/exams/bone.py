"""Bone scintigraphy analyzer (foci + Bone Scan Index).

IMPORTANT — clinical validation required. The validated Bone Scan Index (BSI) is a
fraction of total skeletal *mass* involved by disease, computed by a validated
methodology. This analyzer computes only a transparent **volume-fraction proxy**
from the segmentation (involved skeletal volume / total skeletal volume) and the
count of hyperfixating foci. It is explicitly flagged as NON-validated and must be
reviewed with the nuclear-medicine physician before any clinical use. The proxy is
never presented as the validated BSI.
"""

from __future__ import annotations

from app.models.clinical import Lesion, OrganMeasurement
from app.models.enums import ExamType, ScoreType
from app.services.exams.base import ExamAnalyzer, ExamResult

_DISCLAIMER = (
    "Proxy de fraction volumique squelettique (segmentation) — NON validé "
    "cliniquement. Le Bone Scan Index validé repose sur une méthode dédiée ; "
    "à définir et valider avec le médecin nucléaire."
)


class BoneScanAnalyzer(ExamAnalyzer):
    exam_type = ExamType.bone
    model_version = "bone-proxy-0"

    def analyze(
        self,
        *,
        organs: list[OrganMeasurement],
        lesions: list[Lesion],
    ) -> ExamResult:
        foci = [lesion for lesion in lesions if not lesion.is_physiological]
        total_skeletal_ml = sum(float(o.volume_ml) for o in organs if o.volume_ml is not None)
        involved_names = {f.anatomical_ref for f in foci if f.anatomical_ref}
        involved_ml = sum(
            float(o.volume_ml)
            for o in organs
            if o.organ_name in involved_names and o.volume_ml is not None
        )
        bsi_proxy = (involved_ml / total_skeletal_ml * 100.0) if total_skeletal_ml > 0 else 0.0

        summary = f"{len(foci)} foyer(s) hyperfixant(s) non physiologique(s) recensé(s)."
        details = {
            "n_foci": len(foci),
            "bsi_proxy_pct": round(bsi_proxy, 2),
            "total_skeletal_ml": round(total_skeletal_ml, 1),
            "involved_skeletal_ml": round(involved_ml, 1),
            "method": "proxy_volume_fraction",
            "model_version": self.model_version,
            "needs_clinical_validation": True,
            "disclaimer": _DISCLAIMER,
        }
        return ExamResult(
            score_type=ScoreType.bsi,
            score_value=f"{bsi_proxy:.1f}",
            summary=summary,
            details=details,
        )
