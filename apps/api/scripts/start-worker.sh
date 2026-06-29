#!/bin/sh
# Celery worker — processes async tasks (copy, risk, notifications, billing).
set -eu

CONCURRENCY="${CELERY_CONCURRENCY:-4}"
LOGLEVEL="${CELERY_LOG_LEVEL:-INFO}"
QUEUES="${CELERY_QUEUES:-default,copy,risk,notifications,celery}"

echo "[celery-worker] Starting worker (concurrency=${CONCURRENCY}, queues=${QUEUES})…"

exec celery -A tradeflow.workers.celery_app:celery_app worker \
  --loglevel="${LOGLEVEL}" \
  --concurrency="${CONCURRENCY}" \
  -Q "${QUEUES}" \
  --without-gossip \
  --without-mingle \
  --without-heartbeat
