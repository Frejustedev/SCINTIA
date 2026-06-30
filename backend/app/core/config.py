"""Application configuration, sourced exclusively from environment variables.

No secret is ever hard-coded (see docs/05_CONTRAINTES_SECURITE.md). Values are
read from the process environment / a local `.env` file that is never committed.
"""

from __future__ import annotations

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Typed application settings."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ── Application ──
    app_name: str = "Scintia"
    app_env: str = "development"
    log_level: str = "INFO"
    api_v1_prefix: str = "/api/v1"

    # ── Backend ──
    backend_host: str = "0.0.0.0"
    backend_port: int = 8000
    backend_cors_origins: str = "http://localhost:3000"

    # ── Auth ──
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 720  # 12 h

    # ── Object storage (local volume by default; MinIO later) ──
    storage_dir: str = "data/objects"

    # ── Datastores (not connected in Phase 0, declared for later phases) ──
    database_url: str | None = None
    redis_url: str | None = None
    celery_broker_url: str | None = None
    celery_result_backend: str | None = None

    # ── Secrets (never logged) ──
    secret_key: str | None = Field(default=None, repr=False)
    identity_encryption_key: str | None = Field(default=None, repr=False)
    anthropic_api_key: str | None = Field(default=None, repr=False)

    @property
    def cors_origins(self) -> list[str]:
        """CORS origins as a list (comma-separated in the environment)."""
        return [o.strip() for o in self.backend_cors_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    """Return a cached Settings instance."""
    return Settings()
