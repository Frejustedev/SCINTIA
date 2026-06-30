"""Strategy interface for per-exam analysis (docs/02_ARCHITECTURE.md §3).

Each exam type has its own analyzer (BoneScanAnalyzer, MyocardialSpectAnalyzer,
MibgAnalyzer, OctreotideAnalyzer, ParathyroidAnalyzer, LungVQAnalyzer). Adding an
exam = adding a class, without touching the rest.

Analyzers compute *factual* scores/summaries from the measurements; they never
interpret or diagnose — the physician validates everything.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any

from app.models.clinical import Lesion, OrganMeasurement
from app.models.enums import ExamType, ScoreType


@dataclass(frozen=True)
class ExamResult:
    """Output of an analyzer: a standardized score plus a factual summary."""

    score_type: ScoreType
    score_value: str
    summary: str
    details: dict[str, Any] = field(default_factory=dict)


class ExamAnalyzer(ABC):
    """Common interface for all exam analyzers."""

    exam_type: ExamType
    model_version: str = "abstract"

    @abstractmethod
    def analyze(
        self,
        *,
        organs: list[OrganMeasurement],
        lesions: list[Lesion],
    ) -> ExamResult: ...
