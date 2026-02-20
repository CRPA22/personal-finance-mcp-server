# Multi-stage build
FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim AS builder

WORKDIR /app

COPY pyproject.toml uv.lock README.md ./
RUN uv sync --frozen --no-dev

COPY app/ ./app/
COPY alembic.ini ./
COPY migrations/ ./migrations/

FROM python:3.12-slim

WORKDIR /app

RUN adduser --disabled-password --gecos "" appuser

COPY --from=builder /app/.venv /app/.venv
COPY --from=builder /app/app /app/app
COPY --from=builder /app/alembic.ini /app/alembic.ini
COPY --from=builder /app/migrations /app/migrations
COPY --from=builder /app/pyproject.toml /app/pyproject.toml

ENV PATH="/app/.venv/bin:$PATH"

COPY infra/docker/entrypoint.py /entrypoint.py

USER appuser

ENTRYPOINT ["python", "/entrypoint.py"]
