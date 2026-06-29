#!/bin/sh
# Run Alembic migrations against DATABASE_URL_SYNC.
# Used as Railway preDeployCommand or one-off release job.
set -eu

cd /app

echo "[migrate] Running alembic upgrade head…"
alembic upgrade head
echo "[migrate] Database schema is up to date."
