"""Health endpoint test — the Phase 0 definition-of-done check for the API."""

from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health_returns_200() -> None:
    response = client.get("/health")
    assert response.status_code == 200


def test_health_payload_shape() -> None:
    payload = client.get("/health").json()
    assert payload["status"] == "ok"
    assert payload["app"]
    assert "version" in payload
    assert "environment" in payload
