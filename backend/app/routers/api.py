"""Aggregate router for versioned business endpoints (mounted under /api/v1)."""

from __future__ import annotations

from fastapi import APIRouter

from app.routers import auth, studies, users

api_router = APIRouter()
api_router.include_router(auth.router)
api_router.include_router(users.router)
api_router.include_router(studies.router)
