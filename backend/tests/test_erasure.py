"""Data retention (raw DICOM purge) and right-to-erasure."""

from __future__ import annotations

import uuid

import pytest
from fastapi.testclient import TestClient
from pydicom.uid import generate_uid
from sqlalchemy.orm import Session

from tests.conftest import bootstrap_and_login
from tests.test_ingestion import _dicom_bytes


def _files(study_uid: str) -> list[tuple[str, tuple[str, bytes, str]]]:
    return [
        (
            "files",
            (
                "ct.dcm",
                _dicom_bytes(modality="CT", study_uid=study_uid, series_uid=generate_uid()),
                "application/dicom",
            ),
        ),
        (
            "files",
            (
                "nm.dcm",
                _dicom_bytes(modality="NM", study_uid=study_uid, series_uid=generate_uid()),
                "application/dicom",
            ),
        ),
    ]


def test_erase_study_removes_data_and_identity(
    client: TestClient, db_session: Session, object_storage: object
) -> None:
    from app.models.audit import AuditLog
    from app.models.patient import Patient, PatientIdentity
    from app.models.study import Study

    headers = bootstrap_and_login(client)
    sid = client.post(
        "/api/v1/studies",
        headers=headers,
        json={"exam_type": "bone", "patient": {"name": "DOE^JOHN", "patient_id": "P1"}},
    ).json()["id"]
    study_uid = generate_uid()
    client.post(f"/api/v1/studies/{sid}/files", headers=headers, files=_files(study_uid))
    client.post(f"/api/v1/studies/{sid}/analyze", headers=headers)

    study = db_session.get(Study, uuid.UUID(sid))
    assert study is not None
    pid = study.patient_id
    assert db_session.query(PatientIdentity).filter_by(patient_id=pid).count() == 1

    assert client.delete(f"/api/v1/studies/{sid}", headers=headers).status_code == 204

    db_session.expire_all()
    assert db_session.get(Study, uuid.UUID(sid)) is None
    assert db_session.get(Patient, pid) is None  # patient + encrypted identity gone
    assert db_session.query(PatientIdentity).filter_by(patient_id=pid).count() == 0
    assert client.get(f"/api/v1/studies/{sid}", headers=headers).status_code == 404
    assert db_session.query(AuditLog).filter_by(action="study.erase").count() == 1


def test_manipulateur_cannot_erase(
    client: TestClient, db_session: Session, object_storage: object
) -> None:
    admin = bootstrap_and_login(client)
    client.post(
        "/api/v1/users",
        headers=admin,
        json={
            "email": "m@scintia.fr",
            "full_name": "M",
            "password": "password123",
            "role": "manipulateur",
        },
    )
    token = client.post(
        "/api/v1/auth/login", data={"username": "m@scintia.fr", "password": "password123"}
    ).json()["access_token"]
    manip = {"Authorization": f"Bearer {token}"}
    sid = client.post("/api/v1/studies", headers=manip, json={"exam_type": "bone"}).json()["id"]
    assert client.delete(f"/api/v1/studies/{sid}", headers=manip).status_code == 403


def test_purge_raw_dicom_after_analysis(
    client: TestClient, db_session: Session, object_storage: object, monkeypatch: pytest.MonkeyPatch
) -> None:
    from app.core.config import get_settings
    from app.models.study import StudySeries

    monkeypatch.setenv("PURGE_RAW_DICOM_AFTER_ANALYSIS", "true")
    get_settings.cache_clear()
    try:
        headers = bootstrap_and_login(client)
        sid = client.post("/api/v1/studies", headers=headers, json={"exam_type": "bone"}).json()[
            "id"
        ]
        study_uid = generate_uid()
        client.post(f"/api/v1/studies/{sid}/files", headers=headers, files=_files(study_uid))
        assert (
            client.post(f"/api/v1/studies/{sid}/analyze", headers=headers).json()["status"]
            == "ready"
        )

        db_session.expire_all()
        series = db_session.query(StudySeries).filter_by(study_id=uuid.UUID(sid)).all()
        assert series and all(s.purged for s in series)
        for s in series:
            assert not object_storage.exists(f"{s.storage_path}/0000.dcm")  # type: ignore[attr-defined]
    finally:
        get_settings.cache_clear()
