# Scintia — Backend (FastAPI)

Decision-support backend for nuclear medicine. **Research prototype — not a
certified medical device.**

## Phase 0 scope

Modular skeleton only: `GET /health`, configuration via environment variables,
and the package layout for the processing pipeline. No business logic yet.

## Layout

```
app/
├── main.py        # FastAPI app factory; mounts /health and /api/v1
├── routers/       # HTTP endpoints (health; business routes in later phases)
├── services/      # pipeline services (one service = one role)
│   └── exams/     # per-exam analyzers (strategy pattern)
├── workers/       # Celery app + pipeline tasks (dormant in Phase 0)
├── models/        # SQLAlchemy ORM (data model: docs/04_MODELE_DONNEES.md)
├── schemas/       # Pydantic I/O schemas
└── core/          # config, logging (security/anonymization/audit later)
tests/             # pytest
```

## Local development (network required for installs)

```bash
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
uvicorn app.main:app --reload          # http://localhost:8000/health
pytest                                 # run tests
ruff check . && black --check .        # lint / format
```

Configuration is read from the repo-root `.env` (see `../.env.example`).
