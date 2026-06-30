"""WebSocket progress streaming."""

from __future__ import annotations

import uuid

import pytest
from fastapi.testclient import TestClient
from pydicom.uid import generate_uid
from starlette.websockets import WebSocketDisconnect

from tests.conftest import bootstrap_and_login
from tests.test_ingestion import _dicom_bytes


def test_progress_streams_final_status(
    client: TestClient, db_session: object, object_storage: object
) -> None:
    headers = bootstrap_and_login(client)
    token = headers["Authorization"].split(" ")[1]

    study_id = client.post("/api/v1/studies", headers=headers, json={"exam_type": "bone"}).json()[
        "id"
    ]
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
    ]
    client.post(f"/api/v1/studies/{study_id}/files", headers=headers, files=files)
    client.post(f"/api/v1/studies/{study_id}/analyze", headers=headers)  # synchronous -> ready

    with client.websocket_connect(
        f"/api/v1/studies/{study_id}/progress?token={token}"
    ) as websocket:
        message = websocket.receive_json()
    assert message["status"] == "ready"


def test_progress_rejects_invalid_token(client: TestClient) -> None:
    with pytest.raises(WebSocketDisconnect):
        with client.websocket_connect(
            f"/api/v1/studies/{uuid.uuid4()}/progress?token=bogus"
        ) as websocket:
            websocket.receive_json()
