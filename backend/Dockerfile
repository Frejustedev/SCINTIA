# Scintia backend — FastAPI (Phase 0).
FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# Install dependencies first (better layer caching). Dev extras are included so
# the Phase 0 test (`pytest`) can run inside the container.
COPY pyproject.toml README.md ./
COPY app ./app
RUN pip install --upgrade pip && pip install ".[dev]"

COPY tests ./tests

EXPOSE 8000

# Reload in development for a smoother loop; override the command in production.
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
