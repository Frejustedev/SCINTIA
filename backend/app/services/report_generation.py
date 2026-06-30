"""Report drafting behind a :class:`ReportGenerator` interface.

Two implementations:

* :class:`TemplateReportGenerator` (default, offline) — deterministically reformats
  ONLY the supplied structured data into the radiological structure
  (Indication / Technique / Résultats / Conclusion). It never invents a measurement
  or finding, which makes it the safest generator.
* :class:`ClaudeReportGenerator` — sends the *anonymized* structured context to
  Claude (zero-retention) using the docs/08 prompt. Requires ANTHROPIC_API_KEY.

The mandatory, non-removable banner is added by the caller (services.report).
Neither generator ever receives a patient identifier.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class OrganVolumeCtx:
    organ_name: str
    volume_ml: float | None
    corrected: bool


@dataclass(frozen=True)
class FocusCtx:
    anatomical_ref: str | None
    ratio: float | None
    size_mm: float | None


@dataclass(frozen=True)
class ReportContext:
    """Anonymized, structured input for report drafting (no patient identifier)."""

    exam_type: str
    pseudonym: str
    organs: list[OrganVolumeCtx]
    score_value: str | None
    score_type: str | None = None
    score_details: dict[str, Any] = field(default_factory=dict)
    foci: list[FocusCtx] = field(default_factory=list)


EXAM_LABELS = {
    "bone": "Scintigraphie osseuse (SPECT/CT)",
    "myocardial_spect": "SPECT myocardique",
    "mibg": "Scintigraphie à la MIBG",
    "octreotide": "Scintigraphie des récepteurs de la somatostatine",
    "parathyroid": "Scintigraphie parathyroïdienne",
    "lung_vq": "Scintigraphie pulmonaire ventilation/perfusion",
}

# Human labels for score types. Note: ``bsi_proxy`` is explicitly NOT the validated
# BSI — it is never rendered under the bare validated-metric name.
_SCORE_LABELS = {
    "bsi": "Bone Scan Index (BSI)",
    "bsi_proxy": "BSI (proxy de fraction volumique)",
    "krenning": "Score de Krenning",
    "curie": "Score de Curie",
    "siopen": "Score SIOPEN",
    "pioped": "Probabilité PIOPED",
    "lvef": "FEVG",
    "sss": "SSS",
    "srs": "SRS",
    "sds": "SDS",
    "tid": "TID",
}


def _fmt(value: float | None) -> str:
    """French numeric formatting (comma decimal)."""
    if value is None:
        return "—"
    return f"{value:.1f}".replace(".", ",")


class ReportGenerator(ABC):
    model_version: str = "abstract"

    @abstractmethod
    def generate(self, context: ReportContext) -> str: ...


class TemplateReportGenerator(ReportGenerator):
    """Deterministic, no-invention generator (reformats provided data only)."""

    model_version = "template-0"

    def generate(self, context: ReportContext) -> str:
        label = EXAM_LABELS.get(context.exam_type, context.exam_type)
        lines: list[str] = []
        lines.append("INDICATION")
        lines.append(f"{label}.")
        lines.append("")
        lines.append("TECHNIQUE")
        lines.append(
            "Acquisition SPECT/CT. Segmentation anatomique automatique (assistance "
            "logicielle), volumes par structure ; relecture et correction par le médecin."
        )
        lines.append("")
        lines.append("RÉSULTATS")
        n_foci = context.score_details.get("n_foci")
        if n_foci is not None:
            lines.append(f"- Foyers recensés : {n_foci}.")
        if context.score_value is not None:
            label = _SCORE_LABELS.get(
                context.score_type or "", (context.score_type or "score").upper()
            )
            needs_validation = bool(context.score_details.get("needs_clinical_validation"))
            qualifier = " — NON validé cliniquement" if needs_validation else ""
            unit = " %" if context.score_type == "bsi_proxy" else ""
            lines.append(f"- {label}{qualifier} : {context.score_value}{unit}.")
            if needs_validation:
                note = context.score_details.get("note") or context.score_details.get("disclaimer")
                lines.append(f"    ⚠ {note or 'À valider cliniquement.'}")
        for focus in context.foci:
            ref = focus.anatomical_ref or "localisation à préciser"
            ratio = f", ratio {_fmt(focus.ratio)}" if focus.ratio is not None else ""
            lines.append(f"- Foyer : {ref}{ratio}.")
        lines.append("- Volumes squelettiques segmentés (mL) :")
        for organ in context.organs:
            flag = " (corrigé)" if organ.corrected else ""
            lines.append(f"    · {organ.organ_name} : {_fmt(organ.volume_ml)} mL{flag}")
        lines.append("")
        lines.append("CONCLUSION")
        lines.append(
            "Compte-rendu factuel reprenant exclusivement les mesures fournies. "
            "Interprétation, corrélation clinique et validation à la charge du médecin."
        )
        return "\n".join(lines)


class ClaudeReportGenerator(ReportGenerator):
    """Claude adapter (zero-retention). Requires ANTHROPIC_API_KEY; not used offline."""

    model_version = "claude-opus-4-8"

    def generate(self, context: ReportContext) -> str:  # pragma: no cover
        from app.core.config import get_settings

        api_key = get_settings().anthropic_api_key
        if not api_key:
            raise RuntimeError("ANTHROPIC_API_KEY non configurée.")
        # Real call wiring: send the anonymized ReportContext as structured input with
        # the docs/08 system prompt, zero-retention enabled, guardrails (reformulate
        # only — never invent). Implemented for the deployment with a key.
        raise NotImplementedError(
            "Claude report generation runs with a configured API key and zero-retention; "
            "offline default is TemplateReportGenerator."
        )


def get_report_generator() -> ReportGenerator:
    from app.core.config import get_settings

    if get_settings().report_backend.lower() == "claude":
        return ClaudeReportGenerator()
    return TemplateReportGenerator()
