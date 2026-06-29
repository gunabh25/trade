#!/bin/sh
# Celery beat scheduler — MUST run as exactly one replica in production.
set -eu

LOGLEVEL="${CELERY_LOG_LEVEL:-INFO}"

echo "[celery-beat] Starting beat scheduler…"

exec celery -A tradeflow.workers.celery_app:celery_app beat \
  --loglevel="${LOGLEVEL}" \
  --pidfile=/tmp/celerybeat.pid
