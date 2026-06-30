"""End-to-end pipeline: ingest -> analyze -> results -> report draft (offline)."""

from __future__ import annotations

from fastapi.testclient import TestClient
from pydicom.uid import generate_uid

from tests.conftest import bootstrap_and_login
from tests.test_ingestion import _dicom_bytes


def test_end_to_end_pipeline(
    client: TestClient, db_session: object, object_storage: object
) -> None:
    headers = bootstrap_and_login(client)
    study_id = client.post(
        "/api/v1/studies",
        headers=headers,
        json={"exam_type": "bone", "patient": {"name": "DOE^JOHN", "patient_id": "PID-1"}},
    ).json()["id"]

    study_uid = generate_uid()
    files = [
        (
            "files",
            (
                "ct0.dcm",
                _dicom_bytes(modality="CT", study_uid=study_uid, series_uid=generate_uid()),
                "application/dicom",
            ),
        ),
        (
            "files",
            (
                "nm0.dcm",
                _dicom_bytes(modality="NM", study_uid=study_uid, series_uid=generate_uid()),
                "application/dicom",
            ),
        ),
    ]
    assert (
        client.post(f"/api/v1/studies/{study_id}/files", headers=headers, files=files).status_code
        == 200
    )

    analyzed = client.post(f"/api/v1/studies/{study_id}/analyze", headers=headers)
    assert analyzed.status_code == 200
    assert analyzed.json()["status"] == "ready"

    results = client.get(f"/api/v1/studies/{study_id}/results", headers=headers).json()
    assert len(results["organs"]) == 16
    assert results["score"]["score_type"] == "bsi_proxy"
    assert results["report_status"] == "draft"

    report = client.get(f"/api/v1/studies/{study_id}/report", headers=headers).json()
    assert "Brouillon généré par IA" in report["content"]


def test_analyze_without_ct_conflicts(client: TestClient, object_storage: object) -> None:
    headers = bootstrap_and_login(client)
    study_id = client.post("/api/v1/studies", headers=headers, json={"exam_type": "bone"}).json()[
        "id"
    ]
    assert client.post(f"/api/v1/studies/{study_id}/analyze", headers=headers).status_code == 409
