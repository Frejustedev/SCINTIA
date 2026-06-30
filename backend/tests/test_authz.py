"""Per-study RBAC scoping: a non-clinician only sees their own exams."""

from __future__ import annotations

from fastapi.testclient import TestClient

from tests.conftest import bootstrap_and_login


def _make_user(client: TestClient, admin: dict[str, str], email: str, role: str) -> dict[str, str]:
    client.post(
        "/api/v1/users",
        headers=admin,
        json={"email": email, "full_name": "U", "password": "password123", "role": role},
    )
    token = client.post(
        "/api/v1/auth/login", data={"username": email, "password": "password123"}
    ).json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_per_study_visibility(client: TestClient, db_session: object) -> None:
    admin = bootstrap_and_login(client)
    manip_a = _make_user(client, admin, "a@scintia.fr", "manipulateur")
    manip_b = _make_user(client, admin, "b@scintia.fr", "manipulateur")
    medecin = _make_user(client, admin, "dr@scintia.fr", "medecin")

    sid_a = client.post("/api/v1/studies", headers=manip_a, json={"exam_type": "bone"}).json()["id"]
    sid_b = client.post("/api/v1/studies", headers=manip_b, json={"exam_type": "bone"}).json()["id"]

    # Each manipulateur lists only their own study.
    assert {s["id"] for s in client.get("/api/v1/studies", headers=manip_a).json()} == {sid_a}
    assert {s["id"] for s in client.get("/api/v1/studies", headers=manip_b).json()} == {sid_b}

    # Admin and médecin see both.
    assert {sid_a, sid_b} <= {s["id"] for s in client.get("/api/v1/studies", headers=admin).json()}
    assert {sid_a, sid_b} <= {
        s["id"] for s in client.get("/api/v1/studies", headers=medecin).json()
    }

    # A cannot read B's study (404, not 403 — no existence disclosure).
    assert client.get(f"/api/v1/studies/{sid_b}", headers=manip_a).status_code == 404
    assert client.get(f"/api/v1/studies/{sid_a}", headers=manip_a).status_code == 200
    # The médecin can read both.
    assert client.get(f"/api/v1/studies/{sid_b}", headers=medecin).status_code == 200

    # A cannot drive B's exam either.
    assert client.get(f"/api/v1/studies/{sid_b}/results", headers=manip_a).status_code == 404
    assert client.post(f"/api/v1/studies/{sid_b}/analyze", headers=manip_a).status_code == 404
