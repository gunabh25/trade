#!/bin/sh
set -eu

WORKERS="${API_WORKERS:-1}"
HOST="${API_HOST:-0.0.0.0}"
PORT="${API_PORT:-8000}"
GRACEFUL="${API_GRACEFUL_SHUTDOWN_SECONDS:-30}"

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
