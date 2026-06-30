"""Structured exports (FHIR DiagnosticReport, DICOM-SR) stay pseudonymous."""

from __future__ import annotations

import io

import pydicom
from fastapi.testclient import TestClient
from pydicom.uid import generate_uid
from sqlalchemy.orm import Session

from tests.conftest import bootstrap_and_login
from tests.test_ingestion import _dicom_bytes


def _medecin(client: TestClient, admin: dict[str, str]) -> dict[str, str]:
    client.post(
        "/api/v1/users",
        headers=admin,
        json={
            "email": "dr@scintia.fr",
            "full_name": "Dr",
            "password": "password123",
            "role": "medecin",
        },
    )
    token = client.post(
        "/api/v1/auth/login", data={"username": "dr@scintia.fr", "password": "password123"}
    ).json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def _ready_study(client: TestClient, headers: dict[str, str]) -> str:
    sid = client.post(
        "/api/v1/studies",
        headers=headers,
        json={"exam_type": "bone", "patient": {"name": "DOE^JOHN", "patient_id": "P1"}},
    ).json()["id"]
    su = generate_uid()
    files = [
        (
            "files",
            (
                "ct.dcm",
                _dicom_bytes(modality="CT", study_uid=su, series_uid=generate_uid()),
                "application/dicom",
            ),
        ),
        (
            "files",
            (
                "nm.dcm",
                _dicom_bytes(modality="NM", study_uid=su, series_uid=generate_uid()),
                "application/dicom",
            ),
        ),
    ]
    client.post(f"/api/v1/studies/{sid}/files", headers=headers, files=files)
    client.post(f"/api/v1/studies/{sid}/analyze", headers=headers)
    return sid


def test_fhir_export_is_pseudonymous(
    client: TestClient, db_session: Session, object_storage: object
) -> None:
    admin = bootstrap_and_login(client)
    med = _medecin(client, admin)
    sid = _ready_study(client, med)
    assert client.post(f"/api/v1/studies/{sid}/report/validate", headers=med).status_code == 200

    response = client.get(f"/api/v1/studies/{sid}/export", headers=med, params={"format": "fhir"})
    assert response.status_code == 200
    data = response.json()
    assert data["resourceType"] == "DiagnosticReport"
    assert data["status"] == "final"
    assert data["subject"]["identifier"]["value"].startswith("SC-")
    assert "Brouillon généré par IA" in data["conclusion"]
    assert "DOE" not in response.text  # real identity never leaks


def test_dicom_sr_export_is_pseudonymous(
    client: TestClient, db_session: Session, object_storage: object
) -> None:
    admin = bootstrap_and_login(client)
    med = _medecin(client, admin)
    sid = _ready_study(client, med)

    response = client.get(
        f"/api/v1/studies/{sid}/export", headers=med, params={"format": "dicom-sr"}
    )
    assert response.status_code == 200
    ds = pydicom.dcmread(io.BytesIO(response.content))
    assert ds.Modality == "SR"
    assert str(ds.PatientName).startswith("SC-")
    assert "DOE" not in str(ds.PatientName)
    texts = " ".join(item.TextValue for item in ds.ContentSequence if "TextValue" in item)
    assert "Brouillon généré par IA" in texts
