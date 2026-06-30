"""Integration tests for auth, RBAC and study creation."""

from __future__ import annotations

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from tests.conftest import bootstrap_and_login


def test_bootstrap_login_me_and_create_study(client: TestClient) -> None:
    headers = bootstrap_and_login(client)

    # A second bootstrap is refused once an account exists.
    second = client.post(
        "/api/v1/users/bootstrap-admin",
        json={
            "email": "second@scintia.fr",
            "full_name": "X",
            "password": "password123",
            "role": "admin",
        },
    )
    assert second.status_code == 409

    me = client.get("/api/v1/auth/me", headers=headers)
    assert me.status_code == 200
    assert me.json()["email"] == "admin@scintia.fr"

    created = client.post(
        "/api/v1/studies",
        headers=headers,
        json={
            "exam_type": "bone",
            "patient": {"name": "DOE^JOHN", "birth_date": "19800101", "patient_id": "PID-1"},
        },
    )
    assert created.status_code == 201
    study = created.json()
    assert study["exam_type"] == "bone"
    assert study["status"] == "uploaded"
    assert study["patient_pseudonym"].startswith("SC-")

    study_id = study["id"]
    listed = client.get("/api/v1/studies", headers=headers)
    assert listed.status_code == 200
    assert len(listed.json()) == 1

    fetched = client.get(f"/api/v1/studies/{study_id}", headers=headers)
    assert fetched.status_code == 200
    assert fetched.json()["id"] == study_id


def test_unauthenticated_access_is_rejected(client: TestClient) -> None:
    assert client.get("/api/v1/studies").status_code == 401
    assert client.get("/api/v1/auth/me").status_code == 401


def test_rbac_only_admin_creates_users(client: TestClient) -> None:
    admin_headers = bootstrap_and_login(client)

    # Admin creates a physician.
    created = client.post(
        "/api/v1/users",
        headers=admin_headers,
        json={
            "email": "med@scintia.fr",
            "full_name": "Dr Med",
            "password": "password123",
            "role": "medecin",
        },
    )
    assert created.status_code == 201

    med_token = client.post(
        "/api/v1/auth/login",
        data={"username": "med@scintia.fr", "password": "password123"},
    ).json()["access_token"]
    med_headers = {"Authorization": f"Bearer {med_token}"}

    # A physician cannot manage users ...
    forbidden = client.post(
        "/api/v1/users",
        headers=med_headers,
        json={
            "email": "extra@scintia.fr",
            "full_name": "N",
            "password": "password123",
            "role": "medecin",
        },
    )
    assert forbidden.status_code == 403

    # ... but can create a study.
    assert (
        client.post("/api/v1/studies", headers=med_headers, json={"exam_type": "bone"}).status_code
        == 201
    )


def test_sensitive_actions_are_audited(client: TestClient, db_session: Session) -> None:
    from app.models.audit import AuditLog

    headers = bootstrap_and_login(client)
    client.post("/api/v1/studies", headers=headers, json={"exam_type": "bone"})

    actions = {entry.action for entry in db_session.query(AuditLog).all()}
    assert {"user.bootstrap", "user.login", "study.create"} <= actions


def test_identity_is_stored_encrypted(client: TestClient, db_session: Session) -> None:
    from app.models.patient import PatientIdentity

    headers = bootstrap_and_login(client)
    client.post(
        "/api/v1/studies",
        headers=headers,
        json={"exam_type": "bone", "patient": {"name": "SECRET^NAME", "patient_id": "PID-9"}},
    )
    identities = db_session.query(PatientIdentity).all()
    assert len(identities) == 1
    blob = identities[0].identity_encrypted
    assert isinstance(blob, bytes)
    assert b"SECRET" not in blob  # stored encrypted, not in clear
