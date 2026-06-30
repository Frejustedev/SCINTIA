"""Shared test fixtures: an isolated SQLite database and a wired TestClient."""

from __future__ import annotations

from collections.abc import Iterator

import pytest
from _pytest.monkeypatch import MonkeyPatch
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker


@pytest.fixture(autouse=True)
def _reset_login_limiter() -> Iterator[None]:
    """Keep the in-memory login limiter isolated between tests."""
    from app.core.ratelimit import login_limiter

    login_limiter.clear()
    yield
    login_limiter.clear()


@pytest.fixture
def db_session(tmp_path, monkeypatch: MonkeyPatch) -> Iterator[Session]:
    monkeypatch.setenv("SECRET_KEY", "test-secret-key-0123456789-abcdefghijklmnop")
    monkeypatch.setenv("IDENTITY_ENCRYPTION_KEY", "test-identity-encryption-key-0123456789")

    from app.core.config import get_settings

    get_settings.cache_clear()

    from app.models import Base

    engine = create_engine(
        f"sqlite:///{tmp_path / 'test.db'}",
        connect_args={"check_same_thread": False},
    )
    Base.metadata.create_all(engine)
    testing_session = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
    session = testing_session()
    try:
        yield session
    finally:
        session.close()
        get_settings.cache_clear()


@pytest.fixture
def client(db_session: Session) -> Iterator[TestClient]:
    from app.core.db import get_db
    from app.main import app

    def override_get_db() -> Iterator[Session]:
        try:
            yield db_session
            db_session.commit()
        except Exception:
            db_session.rollback()
            raise

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def object_storage(tmp_path, client: TestClient):  # type: ignore[no-untyped-def]
    """Override the app's object storage with a temp-dir local store."""
    from app.main import app
    from app.services.storage import LocalObjectStorage, get_storage

    storage = LocalObjectStorage(tmp_path / "objects")
    app.dependency_overrides[get_storage] = lambda: storage
    return storage


def bootstrap_and_login(
    client: TestClient,
    *,
    email: str = "admin@scintia.fr",
    password: str = "password123",
) -> dict[str, str]:
    """Create the first admin and return an Authorization header."""
    client.post(
        "/api/v1/users/bootstrap-admin",
        json={"email": email, "full_name": "Admin", "password": password, "role": "admin"},
    )
    token = client.post(
        "/api/v1/auth/login", data={"username": email, "password": password}
    ).json()["access_token"]
    return {"Authorization": f"Bearer {token}"}
