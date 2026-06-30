"""In-memory fixed-window rate limiting for brute-force-sensitive endpoints.

Per-process (sufficient for a single-node prototype); a shared store (Redis) would
back this in a multi-node deployment. Used to throttle login attempts per client IP.
"""

from __future__ import annotations

import time
from collections import defaultdict, deque

from fastapi import HTTPException, Request, status


class FixedWindowLimiter:
    def __init__(self) -> None:
        self._hits: dict[str, deque[float]] = defaultdict(deque)

    def allow(self, key: str, *, limit: int, window_s: float) -> bool:
        now = time.monotonic()
        hits = self._hits[key]
        while hits and hits[0] <= now - window_s:
            hits.popleft()
        if len(hits) >= limit:
            return False
        hits.append(now)
        return True

    def clear(self) -> None:
        self._hits.clear()


login_limiter = FixedWindowLimiter()


def rate_limit_login(request: Request) -> None:
    """FastAPI dependency: throttle login attempts per client IP (no-op if disabled)."""
    from app.core.config import get_settings

    limit = get_settings().login_rate_limit_per_minute
    if limit <= 0:
        return
    client = request.client.host if request.client else "unknown"
    if not login_limiter.allow(client, limit=limit, window_s=60.0):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Trop de tentatives de connexion. Réessayez dans une minute.",
        )
