"""Raw DICOM retention: purge pixel data after analysis (data minimization).

Once analysis has produced the derived results (measurements, score, report —
none of which contain pixel data), the raw de-identified DICOM blobs can be
deleted to minimise stored personal data (docs/05_CONTRAINTES_SECURITE.md).
Controlled by ``settings.purge_raw_dicom_after_analysis``.
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.core.logging import get_logger
from app.models.study import Study
from app.services.storage import ObjectStorage

logger = get_logger(__name__)


def purge_raw_series(db: Session, storage: ObjectStorage, *, study: Study) -> int:
    """Delete the raw DICOM blobs of every series; keep the derived data.

    Returns the number of series purged. Idempotent (already-purged series are
    skipped). A failure to delete one series is logged and never aborts the rest.
    """
    purged = 0
    for series in study.series:
        if series.purged:
            continue
        try:
            storage.delete_prefix(series.storage_path)
        except Exception:  # noqa: BLE001 - best-effort cleanup, logged not fatal
            logger.exception("Failed to purge raw DICOM for series %s", series.id)
            continue
        series.purged = True
        purged += 1
    db.flush()
    return purged
