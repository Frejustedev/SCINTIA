"""Report lifecycle: AI draft, non-removable banner, validation lock, PDF export."""

from __future__ import annotations

import uuid
from decimal import Decimal

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.clinical import OrganMeasurement
from app.models.study import Study
from tests.conftest import bootstrap_and_login

_BANNER = "Brouillon généré par IA"


def _make_medecin_headers(client: TestClient, admin_headers: dict[str, str]) -> dict[str, str]:
    client.post(
        "/api/v1/users",
        headers=admin_headers,
        json={
            "email": "med@scintia.fr",
            "full_name": "Dr Med",
            "password": "password123",
            "role": "medecin",
        },
    )
    token = client.post(
        "/api/v1/auth/login", data={"username": "med@scintia.fr", "password": "password123"}
    ).json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_full_report_flow(client: TestClient, db_session: Session) -> None:
    admin_headers = bootstrap_and_login(client)
    headers = _make_medecin_headers(client, admin_headers)

    study_id = client.post(
        "/api/v1/studies",
        headers=headers,
        json={"exam_type": "bone", "patient": {"name": "DOE^JOHN", "patient_id": "PID-1"}},
    ).json()["id"]

    study = db_session.get(Study, uuid.UUID(study_id))
    assert study is not None
    db_session.add_all(
        [
            OrganMeasurement(study_id=study.id, organ_name="vertebrae_L3", volume_ml=Decimal("40")),
            OrganMeasurement(study_id=study.id, organ_name="sacrum", volume_ml=Decimal("60")),
        ]
    )
    db_session.commit()

    drafted = client.post(f"/api/v1/studies/{study_id}/report", headers=headers)
    assert drafted.status_code == 201
    draft = drafted.json()
    assert draft["status"] == "draft"
    assert _BANNER in draft["content"]
    assert "vertebrae_L3" in draft["content"]

    # Editing without the banner: it is re-added (non-removable).
    edited = client.patch(
        f"/api/v1/studies/{study_id}/report",
        headers=headers,
        json={"content": "RÉSULTATS\nObservations du médecin."},
    )
    assert edited.status_code == 200
    assert edited.json()["status"] == "edited"
    assert _BANNER in edited.json()["content"]

    # Export is refused before validation.
    assert client.get(f"/api/v1/studies/{study_id}/export", headers=headers).status_code == 409

    validated = client.post(f"/api/v1/studies/{study_id}/report/validate", headers=headers)
    assert validated.status_code == 200
    assert validated.json()["status"] == "validated"
    assert validated.json()["validated_by"] is not None

    # The validated report is locked.
    assert (
        client.patch(
            f"/api/v1/studies/{study_id}/report", headers=headers, json={"content": "x"}
        ).status_code
        == 409
    )

    # PDF export (identity re-identified locally into the header).
    exported = client.get(f"/api/v1/studies/{study_id}/export", headers=headers)
    assert exported.status_code == 200
    assert exported.headers["content-type"] == "application/pdf"
    assert exported.content[:4] == b"%PDF"


def test_only_medecin_can_validate(client: TestClient) -> None:
    admin_headers = bootstrap_and_login(client)
    study_id = client.post(
        "/api/v1/studies", headers=admin_headers, json={"exam_type": "bone"}
    ).json()["id"]
    client.post(f"/api/v1/studies/{study_id}/report", headers=admin_headers)
    refused = client.post(f"/api/v1/studies/{study_id}/report/validate", headers=admin_headers)
    assert refused.status_code == 403
