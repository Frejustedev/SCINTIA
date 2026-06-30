"""Celery tasks wrapping the pipeline (production execution path).

Not exercised offline (no broker/DB); the same ``run_pipeline`` is unit-tested
synchronously. On a deployed stack the API enqueues ``run_pipeline_task`` so the
long GPU segmentation runs off the request thread.
"""

from __future__ import annotations

import uuid

from app.workers.celery_app import celery_app


@celery_app.task(name="scintia.run_pipeline")  # type: ignore[untyped-decorator]
def run_pipeline_task(study_id: str) -> str:  # pragma: no cover
    from app.core.db import SessionLocal, get_engine
    from app.models.study import Study
    from app.services.pipeline import run_pipeline
    from app.services.report_generation import get_report_generator
    from app.services.segmentation import get_segmenter
    from app.services.storage import get_storage

    session = SessionLocal(bind=get_engine())
    try:
        study = session.get(Study, uuid.UUID(study_id))
        if study is None:
            return "not_found"
        run_pipeline(
            session,
            get_storage(),
            study=study,
            segmenter=get_segmenter(),
            generator=get_report_generator(),
        )
        session.commit()
        return study.status.value
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
