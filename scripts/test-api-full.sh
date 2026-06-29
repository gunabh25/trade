#!/usr/bin/env bash
# Start Postgres + Redis, migrate, then run the full API test suite.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

cd "${ROOT}"

if ! command -v docker >/dev/null 2>&1; then
  echo "Docker is required for full API tests. Alternatively run: ./scripts/test-api.sh"
  exit 1
fi

echo "Starting PostgreSQL and Redis…"
docker compose up -d postgres redis

echo "Waiting for PostgreSQL…"
for _ in $(seq 1 30); do
  if docker compose exec -T postgres pg_isready -U tradeflow -d tradeflow >/dev/null 2>&1; then
    break
  fi
  sleep 1
done

if ! docker compose exec -T postgres pg_isready -U tradeflow -d tradeflow >/dev/null 2>&1; then
  echo "PostgreSQL did not become ready in time."
  exit 1
fi

cd "${ROOT}/apps/api"
echo "Running migrations…"
alembic upgrade head

echo "Running full pytest suite…"
pytest "$@"
