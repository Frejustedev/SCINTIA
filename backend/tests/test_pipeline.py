"""End-to-end pipeline: ingest -> analyze -> results -> report draft (offline)."""

from __future__ import annotations

import pytest
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


def test_analyze_enqueues_when_broker_configured(
    client: TestClient, object_storage: object, monkeypatch: pytest.MonkeyPatch
) -> None:
    import app.workers.tasks as tasks
    from app.core.config import get_settings

    enqueued: list[str] = []

    class _FakeTask:
        def delay(self, study_id: str) -> None:
            enqueued.append(study_id)

    monkeypatch.setattr(tasks, "run_pipeline_task", _FakeTask())
    monkeypatch.setenv("CELERY_BROKER_URL", "redis://localhost:6379/0")
    get_settings.cache_clear()
    try:
        headers = bootstrap_and_login(client)
        study_id = client.post(
            "/api/v1/studies", headers=headers, json={"exam_type": "bone"}
        ).json()["id"]
        study_uid = generate_uid()
        files = [
            (
                "files",
                (
                    "ct.dcm",
                    _dicom_bytes(modality="CT", study_uid=study_uid, series_uid=generate_uid()),
                    "application/dicom",
                ),
            ),
        ]
        client.post(f"/api/v1/studies/{study_id}/files", headers=headers, files=files)

        response = client.post(f"/api/v1/studies/{study_id}/analyze", headers=headers)
        assert response.status_code == 200
        assert enqueued == [study_id]  # enqueued, not run synchronously

        # The pipeline did NOT run inline, so there are no measurements yet.
        results = client.get(f"/api/v1/studies/{study_id}/results", headers=headers).json()
        assert len(results["organs"]) == 0
    finally:
        get_settings.cache_clear()
