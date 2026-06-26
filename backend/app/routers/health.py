"""Health/liveness endpoint."""

from __future__ import annotations

from fastapi import APIRouter

from app import __version__
from app.core.config import get_settings
from app.schemas.health import HealthResponse

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    """Return service liveness. Always 200 when the process is up."""
    settings = get_settings()
    return HealthResponse(
        status="ok",
        app=settings.app_name,
        version=__version__,
        environment=settings.app_env,
    )
