# RISK MINER backend (api + worker). Build context = repo root (see docker-compose.yml).
FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PYTHON_DOWNLOADS=never

# curl: container healthcheck; tesseract-ocr(-pol): OCR of scans (Apache-2.0); libpq not needed (psycopg[binary]);
# no GPL tooling (no ghostscript/ocrmypdf).
RUN apt-get update && apt-get install -y --no-install-recommends curl ca-certificates tzdata tesseract-ocr tesseract-ocr-pol \
    && rm -rf /var/lib/apt/lists/*
ENV TZ=Europe/Warsaw

COPY --from=ghcr.io/astral-sh/uv:0.5.11 /uv /usr/local/bin/uv

WORKDIR /app/backend
# 1) dependencies only (cached layer)
COPY backend/pyproject.toml backend/uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project
# 2) project code + repo-level files the app reads (REPO_ROOT = /app)
COPY backend/ ./
COPY knowledge/ /app/knowledge/
COPY config/settings.example.yaml /app/config/settings.example.yaml
RUN uv sync --frozen --no-dev && mkdir -p /app/data /app/exports

ENV PATH="/app/backend/.venv/bin:$PATH"
EXPOSE 8040
HEALTHCHECK --interval=15s --timeout=5s --start-period=30s --retries=5 \
    CMD curl -fsS http://localhost:8040/api/health || exit 1
CMD ["sh", "-c", "alembic upgrade head && uvicorn riskminer.api.main:app --host 0.0.0.0 --port 8040 --proxy-headers --forwarded-allow-ips='*'"]
