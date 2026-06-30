"""Pipeline orchestration: chain the analysis steps and drive the status machine.

Runs synchronously here (callable from the API and from tests, offline with the
stub segmenter + template generator). In production the same function is invoked
from a Celery task (app.workers.tasks) so long GPU work happens off the request.

Status machine (docs/02_ARCHITECTURE.md):
uploaded -> anonymizing -> separating -> segmenting -> quantifying -> analyzing
-> generating_report -> ready  (or `error` at any step).
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.models.enums import StudyStatus
from app.models.study import Study
from app.services.analysis import run_analysis
from app.services.report import generate_report
from app.services.report_generation import ReportGenerator
from app.services.segmentation import Segmenter, run_segmentation
from app.services.storage import ObjectStorage


def run_pipeline(
    db: Session,
    storage: ObjectStorage,
    *,
    study: Study,
    segmenter: Segmenter,
    generator: ReportGenerator,
) -> Study:
    """Run segmentation -> quantification -> analysis -> report drafting."""
    try:
        run_segmentation(db, storage, study=study, segmenter=segmenter)

        # Quantification: real sampling of SPECT counts inside the CT masks runs on
        # image data (GPU/real DICOM). Offline, the volumes stand; we still advance
        # the state machine so the pipeline shape is exercised end to end.
        study.status = StudyStatus.quantifying
        db.flush()

        run_analysis(db, study=study)
        generate_report(db, study=study, generator=generator)  # sets status -> ready
        return study
    except Exception as exc:
        study.status = StudyStatus.error
        study.error_message = str(exc)
        db.flush()
        raise
