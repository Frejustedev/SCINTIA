"""Right-to-erasure (RGPD / loi 18-07): irreversibly remove a study.

Erasing a study deletes its storage (raw + derived blobs) and every derived row.
If the patient has no remaining study, the encrypted real identity is deleted
too — which permanently breaks any re-identification of the remaining pseudonymous
data. The append-only audit log is preserved (its link to the study is nulled).
"""

from __future__ import annotations

import uuid

from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session

from app.core.audit import record_audit
from app.models.clinical import DosimetryResult, ExamScore, Lesion, OrganMeasurement
from app.models.patient import Patient
from app.models.report import Report
from app.models.study import Study
from app.services.storage import ObjectStorage


def erase_study(
    db: Session,
    storage: ObjectStorage,
    *,
    study: Study,
    actor_id: uuid.UUID,
) -> dict[str, bool]:
    """Erase a study and, if its patient is left with none, the encrypted identity."""
    study_id = study.id
    patient_id = study.patient_id
    pseudonym = study.patient.pseudonym

    # 1) Storage: raw DICOM, masks, any derived artifact under the study prefix.
    storage.delete_prefix(f"studies/{study_id}")

    # 2) Derived rows. Explicit deletes (DB-agnostic: SQLite enforces no FKs in tests).
    for model in (OrganMeasurement, Lesion, ExamScore, DosimetryResult):
        db.execute(delete(model).where(model.study_id == study_id))
    report = db.scalar(select(Report).where(Report.study_id == study_id))
    if report is not None:
        db.delete(report)  # ORM cascade removes report_versions
    db.flush()

    # 3) The study itself (ORM cascade removes its series rows).
    db.delete(study)
    db.flush()

    # 4) The encrypted identity, only if the patient has no remaining study.
    remaining = (
        db.scalar(select(func.count()).select_from(Study).where(Study.patient_id == patient_id))
        or 0
    )
    identity_erased = False
    if remaining == 0:
        patient = db.get(Patient, patient_id)
        if patient is not None:
            db.delete(patient)  # cascade removes the encrypted PatientIdentity
            identity_erased = True
        db.flush()

    # The pseudonym is non-significant (not personal data); safe to log.
    record_audit(
        db,
        action="study.erase",
        user_id=actor_id,
        study_id=None,
        details={"pseudonym": pseudonym, "identity_erased": identity_erased},
    )
    return {"identity_erased": identity_erased}
