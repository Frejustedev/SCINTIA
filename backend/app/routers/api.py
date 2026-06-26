"""Aggregate router for versioned business endpoints (mounted under /api/v1).

Empty in Phase 0. Pipeline endpoints (studies, reports, calibration, auth,
export — see docs/02_ARCHITECTURE.md §5) are added in later phases.
"""

from __future__ import annotations

from fastapi import APIRouter

api_router = APIRouter()

# Future routers are included here, e.g.:
#     from app.routers import studies
#     api_router.include_router(studies.router)
