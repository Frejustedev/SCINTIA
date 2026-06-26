"""Celery application instance (broker/result backend from environment).

No tasks are registered in Phase 0. The async pipeline (chained tasks with
real-time progress over Redis) is built in Phase 1.
"""

from __future__ import annotations

from celery import Celery

from app.core.config import get_settings

_settings = get_settings()

celery_app = Celery(
    "scintia",
    broker=_settings.celery_broker_url or _settings.redis_url,
    backend=_settings.celery_result_backend,
)
celery_app.conf.update(
    task_track_started=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
)
