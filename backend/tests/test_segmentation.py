"""Segmentation: stub volumes, listing, and mandatory manual correction."""

from __future__ import annotations

import uuid

import pytest
from fastapi.testclient import TestClient
from pydicom.uid import generate_uid
from sqlalchemy.orm import Session

from app.models.study import Study
from app.services.segmentation import StubSegmenter, run_segmentation
from tests.conftest import bootstrap_and_login
from tests.test_ingestion import _dicom_bytes


def _ingest_ct_study(client: TestClient, headers: dict[str, str]) -> str:
    study_id: str = client.post(
        "/api/v1/studies", headers=headers, json={"exam_type": "bone"}
    ).json()["id"]
    study_uid = generate_uid()
    ct_series = generate_uid()
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
    ]
    client.post(f"/api/v1/studies/{study_id}/files", headers=headers, files=files)
    return study_id


def test_segmentation_creates_volumes_and_allows_correction(
    client: TestClient, db_session: Session, object_storage: object
) -> None:
    headers = bootstrap_and_login(client)
    study_id = _ingest_ct_study(client, headers)

    study = db_session.get(Study, uuid.UUID(study_id))
    assert study is not None
    measurements = run_segmentation(
        db_session, object_storage, study=study, segmenter=StubSegmenter()  # type: ignore[arg-type]
    )
    db_session.commit()
    assert len(measurements) == 16

    listed = client.get(f"/api/v1/studies/{study_id}/segmentation", headers=headers)
    assert listed.status_code == 200
    rows = listed.json()
    assert len(rows) == 16
    assert all(not row["segmentation_corrected"] for row in rows)

    measurement_id = rows[0]["id"]
    patched = client.patch(
        f"/api/v1/studies/{study_id}/measurements/{measurement_id}",
        headers=headers,
        json={"volume_ml": "123.4"},
    )
    assert patched.status_code == 200
    body = patched.json()
    assert body["segmentation_corrected"] is True
    assert float(body["volume_ml"]) == 123.4


def test_segmentation_without_ct_raises(
    client: TestClient, db_session: Session, object_storage: object
) -> None:
    headers = bootstrap_and_login(client)
    study_id = client.post("/api/v1/studies", headers=headers, json={"exam_type": "bone"}).json()[
        "id"
    ]
    study = db_session.get(Study, uuid.UUID(study_id))
    assert study is not None
    with pytest.raises(ValueError):
        run_segmentation(
            db_session, object_storage, study=study, segmenter=StubSegmenter()  # type: ignore[arg-type]
        )
