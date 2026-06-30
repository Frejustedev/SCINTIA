"""Viewer support: series listing and de-identified instance serving."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from pydicom.uid import generate_uid
from sqlalchemy.orm import Session

from tests.conftest import bootstrap_and_login
from tests.test_ingestion import _dicom_bytes


def _upload_ct_nm(client: TestClient, headers: dict[str, str], sid: str) -> None:
    su, ct = generate_uid(), generate_uid()
    files = [
        (
            "files",
            (
                "ct0.dcm",
                _dicom_bytes(modality="CT", study_uid=su, series_uid=ct),
                "application/dicom",
            ),
        ),
        (
            "files",
            (
                "ct1.dcm",
                _dicom_bytes(modality="CT", study_uid=su, series_uid=ct),
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


def test_series_listing_and_instance_serving(
    client: TestClient, db_session: Session, object_storage: object
) -> None:
    headers = bootstrap_and_login(client)
    sid = client.post("/api/v1/studies", headers=headers, json={"exam_type": "bone"}).json()["id"]
    _upload_ct_nm(client, headers, sid)

    series = client.get(f"/api/v1/studies/{sid}/series", headers=headers).json()
    assert {s["kind"] for s in series} == {"ct", "spect"}
    ct_series = next(s for s in series if s["kind"] == "ct")
    assert ct_series["instances"] == 2 and ct_series["purged"] is False

    instance = client.get(
        f"/api/v1/studies/{sid}/series/{ct_series['id']}/instances/0", headers=headers
    )
    assert instance.status_code == 200
    assert instance.headers["content-type"].startswith("application/dicom")
    assert instance.content[128:132] == b"DICM"  # valid DICOM preamble

    missing = client.get(
        f"/api/v1/studies/{sid}/series/{ct_series['id']}/instances/9", headers=headers
    )
    assert missing.status_code == 404

    # The viewer fetches rendered PNG frames (window/level applied server-side).
    frame = client.get(f"/api/v1/studies/{sid}/series/{ct_series['id']}/frames/0", headers=headers)
    assert frame.status_code == 200
    assert frame.headers["content-type"] == "image/png"
    assert frame.content[:8] == b"\x89PNG\r\n\x1a\n"


def test_instance_gone_when_purged(
    client: TestClient, db_session: Session, object_storage: object, monkeypatch: pytest.MonkeyPatch
) -> None:
    from app.core.config import get_settings

    monkeypatch.setenv("PURGE_RAW_DICOM_AFTER_ANALYSIS", "true")
    get_settings.cache_clear()
    try:
        headers = bootstrap_and_login(client)
        sid = client.post("/api/v1/studies", headers=headers, json={"exam_type": "bone"}).json()[
            "id"
        ]
        _upload_ct_nm(client, headers, sid)
        ct_series = next(
            s
            for s in client.get(f"/api/v1/studies/{sid}/series", headers=headers).json()
            if s["kind"] == "ct"
        )
        client.post(f"/api/v1/studies/{sid}/analyze", headers=headers)  # triggers purge

        gone = client.get(
            f"/api/v1/studies/{sid}/series/{ct_series['id']}/instances/0", headers=headers
        )
        assert gone.status_code == 410
    finally:
        get_settings.cache_clear()
