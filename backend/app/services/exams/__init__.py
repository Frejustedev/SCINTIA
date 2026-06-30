"""Per-exam analyzers (strategy pattern). Adding an exam = registering a class.

Each exam type implements the common ``ExamAnalyzer`` interface so a new exam is
added without touching the rest (docs/02_ARCHITECTURE.md §3). Only the bone scan
computes a (transparent, flagged) score today; the others are frameworks that
extract the factual findings and flag the validated clinical score for the
physician — they never fabricate a clinical score.
"""

from __future__ import annotations

from app.models.enums import ExamType
from app.services.exams.base import ExamAnalyzer, ExamResult
from app.services.exams.bone import BoneScanAnalyzer
from app.services.exams.lung_vq import LungVQAnalyzer
from app.services.exams.mibg import MibgAnalyzer
from app.services.exams.myocardial import MyocardialSpectAnalyzer
from app.services.exams.octreotide import OctreotideAnalyzer
from app.services.exams.parathyroid import ParathyroidAnalyzer

_ANALYZERS: dict[ExamType, type[ExamAnalyzer]] = {
    ExamType.bone: BoneScanAnalyzer,
    ExamType.myocardial_spect: MyocardialSpectAnalyzer,
    ExamType.mibg: MibgAnalyzer,
    ExamType.octreotide: OctreotideAnalyzer,
    ExamType.parathyroid: ParathyroidAnalyzer,
    ExamType.lung_vq: LungVQAnalyzer,
}


def get_analyzer(exam_type: ExamType) -> ExamAnalyzer:
    """Return the analyzer for an exam type."""
    analyzer_cls = _ANALYZERS.get(exam_type)
    if analyzer_cls is None:
        raise NotImplementedError(f"Aucun analyseur pour l'examen « {exam_type.value} ».")
    return analyzer_cls()


__all__ = [
    "BoneScanAnalyzer",
    "ExamAnalyzer",
    "ExamResult",
    "LungVQAnalyzer",
    "MibgAnalyzer",
    "MyocardialSpectAnalyzer",
    "OctreotideAnalyzer",
    "ParathyroidAnalyzer",
    "get_analyzer",
]
