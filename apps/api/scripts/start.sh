#!/bin/sh
# Production API entrypoint — supports Railway $PORT and optional startup migrations.
set -eu

WORKERS="${API_WORKERS:-1}"
HOST="${API_HOST:-0.0.0.0}"
# Railway injects PORT; fall back to API_PORT then 8000.
PORT="${PORT:-${API_PORT:-8000}}"
GRACEFUL="${API_GRACEFUL_SHUTDOWN_SECONDS:-30}"
RUN_MIGRATIONS="${RUN_MIGRATIONS_ON_START:-false}"

if [ "$RUN_MIGRATIONS" = "true" ]; then
  echo "[api] Running migrations before startup…"
  alembic upgrade head
fi

echo "[api] Starting uvicorn on ${HOST}:${PORT} (workers=${WORKERS})…"

if [ "$WORKERS" -gt 1 ]; then
  exec uvicorn tradeflow.main:app \
    --host "$HOST" \
    --port "$PORT" \
    --app-dir src \
    --workers "$WORKERS" \
    --timeout-graceful-shutdown "$GRACEFUL" \
    --proxy-headers \
    --forwarded-allow-ips='*'
fi

exec uvicorn tradeflow.main:app \
  --host "$HOST" \
  --port "$PORT" \
  --app-dir src \
  --timeout-graceful-shutdown "$GRACEFUL" \
  --proxy-headers \
  --forwarded-allow-ips='*'
