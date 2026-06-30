"""Celery application instance (broker/result backend from environment).

The pipeline task lives in ``app.workers.tasks`` and is registered via
``include`` so a worker started with ``-A app.workers.celery_app:celery_app``
discovers it without importing the module by hand.
"""

from __future__ import annotations

from celery import Celery

from app.core.config import get_settings

_settings = get_settings()

celery_app = Celery(
    "scintia",
    broker=_settings.celery_broker_url or _settings.redis_url,
    backend=_settings.celery_result_backend,
    include=["app.workers.tasks"],
)
celery_app.conf.update(
    task_track_started=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
)
