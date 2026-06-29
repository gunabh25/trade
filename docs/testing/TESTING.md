# Testing Guide

TradeFlow AI uses a layered testing strategy targeting **90%+ coverage** across backend and frontend.

## Backend (Pytest)

Location: `apps/api/tests/`

| Layer       | Directory / marker                               | Description                                                 |
| ----------- | ------------------------------------------------ | ----------------------------------------------------------- |
| Unit        | `tests/unit/`, `@pytest.mark.unit`               | Pure logic — middleware, OMS, risk, copy engine, broker SDK |
| Integration | `tests/integration/`, `@pytest.mark.integration` | PostgreSQL flows — auth, billing                            |
| API         | `tests/api/`, `@pytest.mark.api`                 | HTTP endpoints — admin, dashboard, notifications            |

### Support modules

- `tests/support/factories.py` — test data builders
- `tests/support/mocks.py` — Stripe, email, broker mocks
- `tests/support/auth_helpers.py` — register/login helpers

### Run locally

**No database required** — unit tests and most API smoke tests work offline:

```bash
cd apps/api
pip install -e ".[dev]"
pytest                    # integration tests auto-skip when Postgres is down
# or from repo root:
pnpm test:api
pnpm test:api:unit        # unit tests only
```

**Full suite (integration + migrations)** — start Postgres and Redis first:

```bash
# From repo root — starts docker compose, migrates, runs pytest
pnpm test:api:full

# Manual equivalent:
docker compose up -d postgres redis
cd apps/api && alembic upgrade head && pytest
```

> **Note:** `alembic upgrade head` requires a running PostgreSQL instance. If you only run `pytest`, integration tests skip gracefully when the database is unavailable (~152 pass, ~12 skip).

### Coverage gates

```bash
cd apps/api

# Critical modules — 90% gate
pnpm test:api -- critical   # or: bash ../../scripts/test-api.sh critical

# Full HTML coverage report
pnpm test:api -- coverage
```

HTML coverage report: `apps/api/htmlcov/index.html`

### By marker

```bash
pytest -m unit
pytest -m integration   # requires Postgres + migrations
pytest -m api
```

## Frontend (Vitest + React Testing Library)

Location: `apps/web/src/**/*.test.{ts,tsx}`

```bash
cd apps/web
pnpm test              # single run
pnpm test:watch        # watch mode
pnpm test:coverage     # with 90% thresholds on lib + admin-ui
```

## E2E (Playwright)

Location: `apps/web/e2e/`

```bash
cd apps/web
pnpm exec playwright install chromium
pnpm test:e2e
```

Playwright starts the Next.js dev server locally (production build in CI).

Report: `apps/web/playwright-report/index.html`

## Monorepo scripts

From repository root:

```bash
pnpm test              # Vitest (web) — no database needed
pnpm test:coverage     # Vitest with coverage
pnpm test:api          # Pytest (skips integration if DB down)
pnpm test:api:full     # Docker Postgres/Redis + migrate + full pytest
pnpm test:e2e          # Playwright E2E
pnpm test:all          # Everything above in sequence
```

## CI

GitHub Actions (`.github/workflows/ci.yml`):

1. **Python API** — Ruff, Mypy, Alembic migrations, Pytest with coverage artifacts
2. **Frontend tests** — Vitest + coverage
3. **Playwright** — smoke tests for auth, dashboard, admin
4. **Docker** — builds after tests pass

Coverage artifacts are uploaded for PR review.

## Coverage targets

| Area                   | Tool         | Threshold                                                                  |
| ---------------------- | ------------ | -------------------------------------------------------------------------- |
| API critical modules   | pytest-cov   | **90%** (copy engine sizing/types, JWT, middleware, templates, risk types) |
| API full codebase      | pytest-cov   | Report only (track progress toward 90%)                                    |
| Web utilities (`lib/`) | Vitest v8    | **90%** lines / functions                                                  |
| Web components         | Vitest + RTL | Tested (admin-ui); expand for full 90% component coverage                  |

## Domains covered

- Authentication (unit + integration + E2E)
- Trade Copier / copy engine
- Risk engine
- OMS / paper broker order lifecycle
- Broker SDK & market data capabilities
- Dashboard / analytics API
- Notifications API
- Billing API & Stripe dev mode
- Admin API & UI components
