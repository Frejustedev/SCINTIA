"""DICOM ingestion: CT/SPECT separation, de-identification, storage."""

from __future__ import annotations

import io
import uuid
import zipfile

import numpy as np
import pydicom
from fastapi.testclient import TestClient
from pydicom.dataset import Dataset, FileMetaDataset
from pydicom.uid import CTImageStorage, ExplicitVRLittleEndian, generate_uid
from sqlalchemy.orm import Session

from tests.conftest import bootstrap_and_login


def _dicom_bytes(*, modality: str, study_uid: str, series_uid: str) -> bytes:
    ds = Dataset()
    ds.PatientName = "DOE^JOHN"
    ds.PatientID = "PID-1"
    ds.PatientBirthDate = "19800101"
    ds.InstitutionName = "Hopital Central"
    ds.Modality = modality
    ds.StudyInstanceUID = study_uid
    ds.SeriesInstanceUID = series_uid
    ds.SOPInstanceUID = generate_uid()
    ds.SOPClassUID = CTImageStorage
    ds.Rows = 2
    ds.Columns = 2
    ds.BitsAllocated = 16
    ds.BitsStored = 16
    ds.HighBit = 15
    ds.SamplesPerPixel = 1
    ds.PhotometricInterpretation = "MONOCHROME2"
    ds.PixelRepresentation = 0
    ds.PixelData = np.zeros((2, 2), dtype=np.uint16).tobytes()

    meta = FileMetaDataset()
    meta.MediaStorageSOPClassUID = CTImageStorage
    meta.MediaStorageSOPInstanceUID = ds.SOPInstanceUID
    meta.TransferSyntaxUID = ExplicitVRLittleEndian
    ds.file_meta = meta

    buffer = io.BytesIO()
    ds.save_as(buffer, enforce_file_format=True)
    return buffer.getvalue()


def test_upload_separates_anonymizes_and_stores(
    client: TestClient, db_session: Session, object_storage: object
) -> None:
    from app.models.study import StudySeries

    headers = bootstrap_and_login(client)
    study_id = client.post("/api/v1/studies", headers=headers, json={"exam_type": "bone"}).json()[
        "id"
    ]

    study_uid = generate_uid()
    ct_series = generate_uid()
    spect_series = generate_uid()
    files = [
        (
            "files",
            (
                "ct0.dcm",
                _dicom_bytes(modality="CT", study_uid=study_uid, series_uid=ct_series),
                "application/dicom",
            ),
        ),
        (
            "files",
            (
                "ct1.dcm",
                _dicom_bytes(modality="CT", study_uid=study_uid, series_uid=ct_series),
                "application/dicom",
            ),
        ),
        (
            "files",
            (
                "nm0.dcm",
                _dicom_bytes(modality="NM", study_uid=study_uid, series_uid=spect_series),
                "application/dicom",
            ),
        ),
        ("files", ("junk.txt", b"not dicom at all", "text/plain")),
    ]
    response = client.post(f"/api/v1/studies/{study_id}/files", headers=headers, files=files)
    assert response.status_code == 200
    summary = response.json()
    assert summary["ct_series"] == 1
    assert summary["spect_series"] == 1
    assert summary["instances"] == 3
    assert summary["skipped"] == 1
    assert summary["status"] == "separating"

    series = db_session.query(StudySeries).filter_by(study_id=uuid.UUID(study_id)).all()
    assert {s.kind.value for s in series} == {"ct", "spect"}
    assert all(s.anonymized for s in series)

    # Stored DICOM is de-identified (no PHI on disk).
    ct = next(s for s in series if s.kind.value == "ct")
    stored = object_storage.read_bytes(f"{ct.storage_path}/0000.dcm")  # type: ignore[attr-defined]
    parsed = pydicom.dcmread(io.BytesIO(stored))
    assert str(parsed.PatientName) == ""
    assert "InstitutionName" not in parsed


def test_upload_with_no_valid_dicom_marks_error(
    client: TestClient, db_session: Session, object_storage: object
) -> None:
    from app.models.study import Study

    headers = bootstrap_and_login(client)
    study_id = client.post("/api/v1/studies", headers=headers, json={"exam_type": "bone"}).json()[
        "id"
    ]
    files = [("files", ("junk.txt", b"nope", "text/plain"))]
    summary = client.post(f"/api/v1/studies/{study_id}/files", headers=headers, files=files).json()
    assert summary["status"] == "error"
    assert summary["instances"] == 0
    assert summary["skipped"] == 1

    study = db_session.get(Study, uuid.UUID(study_id))
    assert study is not None and study.error_message is not None


def test_upload_zip_archive_is_expanded(
    client: TestClient, db_session: Session, object_storage: object
) -> None:
    from app.models.study import StudySeries

    headers = bootstrap_and_login(client)
    study_id = client.post("/api/v1/studies", headers=headers, json={"exam_type": "bone"}).json()[
        "id"
    ]

    study_uid = generate_uid()
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as archive:
        archive.writestr(
            "ct/0.dcm", _dicom_bytes(modality="CT", study_uid=study_uid, series_uid=generate_uid())
        )
        archive.writestr(
            "nm/0.dcm", _dicom_bytes(modality="NM", study_uid=study_uid, series_uid=generate_uid())
        )
        archive.writestr("readme.txt", b"not a dicom file")

    files = [("files", ("export.zip", buffer.getvalue(), "application/zip"))]
    summary = client.post(f"/api/v1/studies/{study_id}/files", headers=headers, files=files).json()
    assert summary["ct_series"] == 1
    assert summary["spect_series"] == 1
    assert summary["instances"] == 2
    assert summary["skipped"] == 1  # the readme

    series = db_session.query(StudySeries).filter_by(study_id=uuid.UUID(study_id)).all()
    assert {s.kind.value for s in series} == {"ct", "spect"}
