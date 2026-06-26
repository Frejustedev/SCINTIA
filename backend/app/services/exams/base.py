"""Strategy interface for per-exam analysis.

Defines the contract only — no clinical logic. Concrete analyzers
(BoneScanAnalyzer, MyocardialSpectAnalyzer, MibgAnalyzer, OctreotideAnalyzer,
ParathyroidAnalyzer, LungVQAnalyzer) arrive in Phase 1+.
"""

from __future__ import annotations

from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class ExamAnalyzer(Protocol):
    """Common interface for all exam analyzers.

    Mirrors ``ExamAnalyzer.analyze(study, organs, quantification, dosimetry)
    -> ExamResult`` from docs/02_ARCHITECTURE.md §3. Concrete signatures are
    typed precisely once the data models exist.
    """

    def analyze(
        self,
        study: Any,
        organs: Any,
        quantification: Any,
        dosimetry: Any | None = None,
    ) -> Any:
        """Apply the exam-specific score/analysis and return an ExamResult."""
        ...
