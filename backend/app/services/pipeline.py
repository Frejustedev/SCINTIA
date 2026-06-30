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

from app.core.audit import record_audit
from app.core.config import get_settings
from app.core.logging import get_logger
from app.models.enums import StudyStatus
from app.models.study import Study
from app.services.analysis import run_analysis
from app.services.report import generate_report
from app.services.report_generation import ReportGenerator
from app.services.retention import purge_raw_series
from app.services.segmentation import Segmenter, run_segmentation
from app.services.storage import ObjectStorage

logger = get_logger(__name__)


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

        # Data minimization: optionally drop the raw DICOM once results exist.
        if get_settings().purge_raw_dicom_after_analysis:
            purged = purge_raw_series(db, storage, study=study)
            if purged:
                record_audit(
                    db, action="dicom.purge", study_id=study.id, details={"series": purged}
                )
        return study
    except Exception:
        # Keep the patient-facing message generic; the detail (which may reference
        # source data) stays in server logs only — never on the study or the socket.
        logger.exception("Pipeline failed for study %s", study.id)
        study.status = StudyStatus.error
        study.error_message = "Échec de l'analyse — voir les journaux serveur."
        db.flush()
        raise
