"""FastAPI application entry point.

Phase 0 exposes only `GET /health` plus an empty, versioned API router so the
URL convention (`/api/v1/...`, see docs/02_ARCHITECTURE.md) is fixed from the
start. No business logic is wired yet.
"""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app import __version__
from app.core.config import get_settings
from app.core.logging import configure_logging, get_logger
from app.routers.api import api_router
from app.routers.health import router as health_router


def create_app() -> FastAPI:
    """Application factory."""
    configure_logging()
    settings = get_settings()
    logger = get_logger(__name__)

    app = FastAPI(
        title=f"{settings.app_name} API",
        version=__version__,
        description=(
            "Decision-support backend for nuclear medicine. "
            "Research prototype — not a certified medical device."
        ),
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Liveness at root; versioned business routes under /api/v1.
    app.include_router(health_router)
    app.include_router(api_router, prefix=settings.api_v1_prefix)

    logger.info("%s API starting (env=%s)", settings.app_name, settings.app_env)
    return app


app = create_app()
