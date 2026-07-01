"""DICOM ingestion: parse, de-identify, separate CT/SPECT, and store.

This is the entry of the pipeline. Every dataset is de-identified *before* being
written to object storage (docs/05_CONTRAINTES_SECURITE.md); raw identifiers never
land on disk. Series are grouped by their (original) SeriesInstanceUID and
classified as CT or SPECT from the DICOM Modality.
"""

from __future__ import annotations

import io
import zipfile
from collections import defaultdict
from dataclasses import dataclass

import pydicom
from pydicom import dcmread
from pydicom.dataset import Dataset
from pydicom.errors import InvalidDicomError
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.crypto import encrypt_identity
from app.core.logging import get_logger
from app.models.enums import SeriesKind, StudyStatus
from app.models.patient import PatientIdentity
from app.models.study import Study, StudySeries
from app.services.anonymization import Deidentifier
from app.services.storage import ObjectStorage

logger = get_logger(__name__)

# Real-world DICOM (GE / Siemens exports, etc.) can carry private elements with a
# non-standard length or value. Tolerate them (convert to UN, warn instead of raise)
# rather than aborting the whole upload — only synthetic test files are spec-perfect.
pydicom.config.convert_wrong_length_to_UN = True
pydicom.config.settings.reading_validation_mode = pydicom.config.WARN

# DICOM Modality → our CT/SPECT classification.
_CT_MODALITIES = {"CT"}
_SPECT_MODALITIES = {"NM", "PT", "ST"}


@dataclass
class IngestionResult:
    ct_series: int = 0
    spect_series: int = 0
    instances: int = 0
    skipped: int = 0


def classify_modality(ds: Dataset) -> SeriesKind | None:
    modality = str(getattr(ds, "Modality", "") or "").upper()
    if modality in _CT_MODALITIES:
        return SeriesKind.ct
    if modality in _SPECT_MODALITIES:
        return SeriesKind.spect
    return None


def read_dataset(blob: bytes) -> Dataset | None:
    """Parse a DICOM blob, returning ``None`` for non-DICOM input."""
    try:
        return dcmread(io.BytesIO(blob))
    except (InvalidDicomError, ValueError, OSError):
        return None


_ZIP_MAGIC = b"PK\x03\x04"


def expand_archives(blobs: list[bytes]) -> list[bytes]:
    """Flatten ZIP archives into their member blobs (folder/ZIP/DICOMDIR uploads).

    Non-archive blobs pass through unchanged. A DICOMDIR index file inside the set
    parses as DICOM but has no Modality, so it is harmlessly skipped downstream.
    """
    expanded: list[bytes] = []
    for blob in blobs:
        if blob[:4] != _ZIP_MAGIC:
            expanded.append(blob)
            continue
        try:
            with zipfile.ZipFile(io.BytesIO(blob)) as archive:
                for name in archive.namelist():
                    if name.endswith("/"):
                        continue
                    expanded.append(archive.read(name))
        except (zipfile.BadZipFile, OSError):
            expanded.append(blob)
    return expanded


def _to_bytes(ds: Dataset) -> bytes:
    buffer = io.BytesIO()
    ds.save_as(buffer, enforce_file_format=True)
    return buffer.getvalue()


def _strip_group_lengths(ds: Dataset) -> None:
    """Remove deprecated group-length elements (element 0x0000).

    Some vendors emit these malformed; they are obsolete and pydicom recomputes
    lengths on write anyway, so removing them avoids write failures. Recurses into
    sequences.
    """
    for tag in [elem.tag for elem in ds if elem.tag.element == 0x0000]:
        del ds[tag]
    for elem in ds:
        if elem.VR == "SQ" and elem.value:
            for item in elem.value:
                _strip_group_lengths(item)


def _store_identity_if_absent(
    db: Session, *, study: Study, identity: dict[str, str], identity_key: str
) -> None:
    if not identity or not identity_key:
        return
    existing = db.scalar(
        select(PatientIdentity).where(PatientIdentity.patient_id == study.patient_id)
    )
    if existing is None:
        db.add(
            PatientIdentity(
                patient_id=study.patient_id,
                identity_encrypted=encrypt_identity(identity, identity_key),
            )
        )
        db.flush()


def ingest_study(
    db: Session,
    storage: ObjectStorage,
    *,
    study: Study,
    blobs: list[bytes],
    identity_key: str,
) -> IngestionResult:
    """De-identify and store the uploaded DICOM, creating CT/SPECT series rows."""
    study.status = StudyStatus.anonymizing
    db.flush()

    result = IngestionResult()
    datasets: list[Dataset] = []
    for blob in expand_archives(blobs):
        ds = read_dataset(blob)
        if ds is None:
            result.skipped += 1
        else:
            datasets.append(ds)

    if not datasets:
        study.status = StudyStatus.error
        study.error_message = "Aucun fichier DICOM valide reçu."
        db.flush()
        return result

    deid = Deidentifier(pseudonym=study.patient.pseudonym)
    _store_identity_if_absent(
        db, study=study, identity=deid.extract_identity(datasets[0]), identity_key=identity_key
    )

    # Group instances by their original SeriesInstanceUID.
    groups: dict[str, list[Dataset]] = defaultdict(list)
    for ds in datasets:
        groups[str(getattr(ds, "SeriesInstanceUID", "") or "unknown")].append(ds)

    study.status = StudyStatus.separating
    db.flush()

    for instances in groups.values():
        kind = classify_modality(instances[0])
        if kind is None:
            result.skipped += len(instances)
            continue

        cleaned: list[Dataset] = []
        for ds in instances:
            try:
                cleaned.append(deid.deidentify(ds))
            except Exception:  # a single malformed instance must not abort the batch
                logger.exception("De-identification failed for an instance; skipping it")
                result.skipped += 1
        if not cleaned:
            continue
        new_series_uid = str(getattr(cleaned[0], "SeriesInstanceUID", "") or "series")
        prefix = f"studies/{study.id}/{kind.value}/{new_series_uid}"
        stored = 0
        for cds in cleaned:
            _strip_group_lengths(cds)
            try:
                blob = _to_bytes(cds)
            except Exception:  # unwritable vendor quirk — skip this instance, keep the rest
                logger.exception("Failed to serialize a de-identified instance; skipping it")
                result.skipped += 1
                continue
            # ``stored`` (not the loop index) keeps the on-disk files contiguous 0000..N.
            storage.save_bytes(f"{prefix}/{stored:04d}.dcm", blob)
            stored += 1
        if stored == 0:
            continue

        db.add(
            StudySeries(
                study_id=study.id,
                kind=kind,
                storage_path=prefix,
                anonymized=True,
                series_metadata={
                    "modality": str(getattr(instances[0], "Modality", "") or ""),
                    "instances": stored,
                },
            )
        )
        result.instances += stored
        if kind is SeriesKind.ct:
            result.ct_series += 1
        else:
            result.spect_series += 1

    db.flush()
    return result
