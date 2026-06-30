"""Longitudinal follow-up: repeat exams of one patient are linked and compared."""

from __future__ import annotations

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


def _run(client: TestClient, headers: dict[str, str], sid: str) -> None:
    client.post(f"/api/v1/studies/{sid}/files", headers=headers, files=_files(generate_uid()))
    client.post(f"/api/v1/studies/{sid}/analyze", headers=headers)


def test_longitudinal_follow_up(
    client: TestClient, db_session: Session, object_storage: object
) -> None:
    headers = bootstrap_and_login(client)
    patient = {"name": "DOE^JOHN", "patient_id": "P-LONG"}

    first = client.post(
        "/api/v1/studies", headers=headers, json={"exam_type": "bone", "patient": patient}
    ).json()
    _run(client, headers, first["id"])

    second = client.post(
        "/api/v1/studies", headers=headers, json={"exam_type": "bone", "patient": patient}
    ).json()
    # Same real patient -> same pseudonymous patient reused (linkage).
    assert second["patient_pseudonym"] == first["patient_pseudonym"]
    _run(client, headers, second["id"])

    # The second exam's history lists the first.
    history = client.get(f"/api/v1/studies/{second['id']}/history", headers=headers).json()
    assert [h["study_id"] for h in history] == [first["id"]]

    # The second report carries a factual ANTÉRIORITÉS section.
    report = client.get(f"/api/v1/studies/{second['id']}/report", headers=headers).json()
    assert "ANTÉRIORITÉS" in report["content"]

    # The first exam has no prior.
    assert client.get(f"/api/v1/studies/{first['id']}/history", headers=headers).json() == []
