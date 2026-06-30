"""Per-exam analyzers (strategy pattern). Adding an exam = registering a class.

Each exam type implements the common ``ExamAnalyzer`` interface so a new exam is
added without touching the rest (docs/02_ARCHITECTURE.md §3).
"""

from __future__ import annotations

from app.models.enums import ExamType
from app.services.exams.base import ExamAnalyzer, ExamResult
from app.services.exams.bone import BoneScanAnalyzer

_ANALYZERS: dict[ExamType, type[ExamAnalyzer]] = {
    ExamType.bone: BoneScanAnalyzer,
}


def get_analyzer(exam_type: ExamType) -> ExamAnalyzer:
    """Return the analyzer for an exam type (others arrive in Phase 3)."""
    analyzer_cls = _ANALYZERS.get(exam_type)
    if analyzer_cls is None:
        raise NotImplementedError(
            f"Aucun analyseur disponible pour l'examen « {exam_type.value} » (Phase 3)."
        )
    return analyzer_cls()


__all__ = ["BoneScanAnalyzer", "ExamAnalyzer", "ExamResult", "get_analyzer"]
