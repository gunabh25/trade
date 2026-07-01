# syntax=docker/dockerfile:1
# Build context: repository root (required for monorepo layout).
# Railway: set Dockerfile path to apps/api/Dockerfile, root directory to / .

FROM python:3.12-slim AS base
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app/src \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    APP_ENV=production
WORKDIR /app

FROM base AS builder
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*
COPY apps/api/pyproject.toml apps/api/README.md ./
COPY apps/api/src ./src
RUN pip install --upgrade pip && pip install .

FROM base AS runtime
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && groupadd --system tradeflow \
    && useradd --system --gid tradeflow --home-dir /app tradeflow \
    && mkdir -p uploads/avatars uploads/journal \
    && chown -R tradeflow:tradeflow /app
COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin
COPY apps/api/src ./src
COPY apps/api/alembic ./alembic
COPY apps/api/alembic.ini ./alembic.ini
COPY apps/api/scripts/start.sh apps/api/scripts/migrate.sh \
     apps/api/scripts/start-worker.sh apps/api/scripts/start-beat.sh \
     apps/api/scripts/promote_admin.py \
     ./scripts/
RUN chmod +x ./scripts/*.sh ./scripts/promote_admin.py
USER tradeflow
EXPOSE 8000
ENV API_HOST=0.0.0.0 \
    API_PORT=8000 \
    API_WORKERS=2
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -fsS "http://127.0.0.1:${PORT:-${API_PORT:-8000}}/api/v1/health/ready" || exit 1
CMD ["./scripts/start.sh"]
