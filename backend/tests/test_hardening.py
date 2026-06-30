"""Security hardening: headers, login rate-limit, refresh tokens, TOTP MFA."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.core import mfa
from tests.conftest import bootstrap_and_login


def _bootstrap(client: TestClient) -> None:
    client.post(
        "/api/v1/users/bootstrap-admin",
        json={
            "email": "admin@scintia.fr",
            "full_name": "Admin",
            "password": "password123",
            "role": "admin",
        },
    )


def _login(client: TestClient, otp: str | None = None) -> dict[str, object]:
    data = {"username": "admin@scintia.fr", "password": "password123"}
    if otp is not None:
        data["otp"] = otp
    return client.post("/api/v1/auth/login", data=data)  # type: ignore[return-value]


def test_security_headers(client: TestClient) -> None:
    response = client.get("/health")
    assert response.headers["X-Content-Type-Options"] == "nosniff"
    assert response.headers["X-Frame-Options"] == "DENY"
    assert response.headers["Referrer-Policy"] == "no-referrer"


def test_login_rate_limit(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    from app.core.config import get_settings

    monkeypatch.setenv("LOGIN_RATE_LIMIT_PER_MINUTE", "2")
    get_settings.cache_clear()
    try:
        _bootstrap(client)
        assert _login(client).status_code == 200
        assert _login(client).status_code == 200
        assert _login(client).status_code == 429  # third attempt throttled
    finally:
        get_settings.cache_clear()


def test_refresh_token_flow(client: TestClient) -> None:
    _bootstrap(client)
    tokens = _login(client).json()
    assert tokens["refresh_token"]

    refreshed = client.post("/api/v1/auth/refresh", json={"refresh_token": tokens["refresh_token"]})
    assert refreshed.status_code == 200
    new_access = refreshed.json()["access_token"]
    me = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {new_access}"})
    assert me.status_code == 200

    # A refresh token must not be accepted as an access credential.
    bad = client.get(
        "/api/v1/auth/me", headers={"Authorization": f"Bearer {tokens['refresh_token']}"}
    )
    assert bad.status_code == 401


def test_mfa_enrollment_and_enforcement(client: TestClient) -> None:
    headers = bootstrap_and_login(client)

    secret = client.post("/api/v1/auth/mfa/setup", headers=headers).json()["secret"]
    enabled = client.post(
        "/api/v1/auth/mfa/enable", headers=headers, json={"code": mfa.totp_now(secret)}
    )
    assert enabled.status_code == 200 and enabled.json()["mfa_enabled"] is True

    # Login now requires a valid TOTP code.
    assert _login(client).status_code == 401
    assert _login(client, otp="000000").status_code == 401
    assert _login(client, otp=mfa.totp_now(secret)).status_code == 200
