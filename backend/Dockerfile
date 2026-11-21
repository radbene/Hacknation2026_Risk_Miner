FROM python:3.12-slim
ENV PYTHONUNBUFFERED=1 UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy
COPY --from=ghcr.io/astral-sh/uv:0.5.11 /uv /usr/local/bin/uv
WORKDIR /app/backend
COPY backend/pyproject.toml backend/uv.lock* ./
RUN uv sync --no-dev --no-install-project || uv sync --no-dev --no-install-project
COPY backend/ ./
RUN uv sync --no-dev
ENV PATH="/app/backend/.venv/bin:$PATH"
WORKDIR /app/backend
