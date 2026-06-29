#!/usr/bin/env bash
# Run API tests. Integration tests auto-skip when PostgreSQL is unavailable.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
API_DIR="${ROOT}/apps/api"

cd "${API_DIR}"

if ! command -v pytest >/dev/null 2>&1; then
  echo "pytest not found — install with: pip install -e \".[dev]\" (from apps/api)"
  exit 1
fi

MODE="${1:-all}"

case "${MODE}" in
  unit)
    echo "Running unit tests only (no database required)…"
    pytest -m unit "$@"
    ;;
  integration)
    echo "Running integration tests (PostgreSQL + Redis required)…"
    pytest -m integration "$@"
    ;;
  coverage)
    echo "Running full suite with coverage report…"
    pytest \
      --cov=tradeflow \
      --cov-report=term-missing \
      --cov-report=html \
      "${@:2}"
    ;;
  critical)
    echo "Running critical-module 90% coverage gate…"
    pytest \
      --cov=tradeflow.engine.sizing \
      --cov=tradeflow.engine.types \
      --cov=tradeflow.notifications.templates \
      --cov=tradeflow.core.security.jwt \
      --cov=tradeflow.core.security_middleware \
      --cov=tradeflow.core.rate_limit_middleware \
      --cov=tradeflow.core.observability.prometheus \
      --cov=tradeflow.risk.types \
      --cov-fail-under=90 \
      -q \
      "${@:2}"
    ;;
  all|*)
    echo "Running full test suite (integration tests skip if DB is down)…"
    pytest "${@:2}"
    ;;
esac
