# TradeFlow AI

Professional cloud-based **multi-account trade copier**, **risk management**, and **trading analytics** platform.

This repository contains the **enterprise-grade foundation** — no product features yet. It is production-ready infrastructure for building TradeFlow AI.

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     TradeFlow AI Monorepo                    │
├─────────────────────────────────────────────────────────────┤
│  apps/web          Next.js 15 · React 19 · Tailwind · shadcn │
│  apps/api          FastAPI · SQLAlchemy 2 · Alembic · Celery │
├─────────────────────────────────────────────────────────────┤
│  packages/ui       Shared component library                  │
│  packages/types    Shared API contract types                 │
│  packages/config   ESLint + TypeScript configs               │
├─────────────────────────────────────────────────────────────┤
│  PostgreSQL 16     System of record                          │
│  Redis 7           Cache · Celery broker                     │
└─────────────────────────────────────────────────────────────┘
```

See [docs/ARCHITECTURE.md](./docs/ARCHITECTURE.md) for detailed architectural decisions.

---

## Tech Stack

| Layer | Technology |
|-------|------------|
| Frontend | Next.js 15, React 19, TypeScript, Tailwind CSS, shadcn/ui |
| Backend | FastAPI, Python 3.12, Pydantic v2, SQLAlchemy 2 |
| Database | PostgreSQL 16, Alembic migrations |
| Cache / Queue | Redis 7, Celery |
| Tooling | pnpm, Turborepo, ESLint, Prettier, Husky, lint-staged |
| Infrastructure | Docker, Docker Compose, GitHub Actions |

---

## Repository Structure

```
.
├── apps/
│   ├── web/                 # Next.js dashboard
│   └── api/                 # FastAPI backend
├── packages/
│   ├── ui/                  # shadcn/ui components
│   ├── types/               # Shared TypeScript types
│   └── config/              # ESLint + TSConfig
├── docs/                    # Architecture & product docs
├── scripts/                 # Dev utilities
├── docker-compose.yml
└── .github/workflows/ci.yml
```

### Feature-Based Folders

**Web** (`apps/web/src/`):
```
features/<domain>/
  api/           # API client functions
  components/    # UI components
lib/
  api/           # HTTP client, versioning
  errors/        # ApiClientError
  logging/       # Structured logger
```

**API** (`apps/api/src/tradeflow/`):
```
features/<domain>/
  router.py      # FastAPI routes
  service.py     # Business logic
  schemas.py     # Pydantic models
core/
  config.py      # Settings (pydantic-settings)
  container.py   # Dependency injection
  logging.py     # structlog
  errors.py      # AppError hierarchy
  exception_handlers.py
  responses.py   # SuccessResponse envelope
  app_factory.py # Application factory
api/v1/          # Version router aggregation
db/              # SQLAlchemy base + session
workers/         # Celery app + tasks
```

---

## Quick Start

### Prerequisites

- Node.js 22+
- pnpm 9+
- Python 3.12+
- Docker & Docker Compose (recommended)

### 1. Clone and configure

```bash
cp .env.example .env
# Edit .env if needed — defaults work for local Docker
```

### 2. Run with Docker (recommended)

```bash
chmod +x scripts/dev.sh
./scripts/dev.sh
```

| Service | URL |
|---------|-----|
| Web | http://localhost:3000 |
| API | http://localhost:8000 |
| Swagger UI | http://localhost:8000/api/docs |
| ReDoc | http://localhost:8000/api/redoc |
| OpenAPI JSON | http://localhost:8000/api/openapi.json |

### 3. Run locally (without Docker)

**Infrastructure:**
```bash
docker compose up postgres redis -d
```

**API:**
```bash
cd apps/api
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
alembic upgrade head
uvicorn tradeflow.main:app --reload --app-dir src --port 8000
```

**Celery worker:**
```bash
cd apps/api
source .venv/bin/activate
celery -A tradeflow.workers.celery_app:celery_app worker --loglevel=INFO
```

**Web:**
```bash
pnpm install
pnpm --filter @tradeflow/types build
pnpm --filter @tradeflow/ui build
pnpm --filter @tradeflow/web dev
```

---

## API Endpoints (v1)

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/v1/health/live` | Liveness probe (process alive) |
| GET | `/api/v1/health/ready` | Readiness probe (DB + Redis) |
| GET | `/api/v1/health/` | Health summary for dashboards |

All successful responses:

```json
{
  "data": { ... },
  "meta": { "requestId": "uuid" }
}
```

All errors:

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Request validation failed",
    "details": [{ "field": "email", "message": "..." }],
    "requestId": "uuid"
  }
}
```

---

## Development Commands

```bash
# Monorepo (TypeScript)
pnpm install
pnpm dev          # Start all TS dev servers via Turborepo
pnpm build        # Build all packages and web
pnpm lint         # ESLint across workspace
pnpm typecheck    # TypeScript check
pnpm format       # Prettier write

# API (Python)
cd apps/api
ruff check src tests
ruff format src tests
mypy src
pytest
alembic revision --autogenerate -m "description"
alembic upgrade head
```

---

## Architectural Decisions

### 1. Hybrid Monorepo (TypeScript + Python)

The frontend shares types and UI via pnpm workspaces. The API is a standalone Python package with its own `pyproject.toml`. This avoids forcing Python into Node tooling while keeping one repository.

### 2. FastAPI Application Factory

`create_app()` in `core/app_factory.py` enables:
- Test isolation with injected containers
- Multiple app instances without global state
- Clean lifespan management for DB/Redis

### 3. Dependency Injection (`dependency-injector`)

Services are constructed by a declarative container. Routes use `@inject` + `Depends(Provide[Container.service])`. Singletons (DB engine, Redis) are created once; services are factories.

### 4. API Versioning (`/api/v1`)

URL-based versioning is explicit and CDN-friendly. The v1 router aggregates feature routers. Future v2 mounts at `/api/v2` without breaking v1 clients.

### 5. Standard Response Envelope

All success responses wrap payload in `{ data, meta }`. This gives room for pagination metadata, request IDs, and consistent client parsing in `@tradeflow/types`.

### 6. Centralized Error Handling

`AppError` subclasses map to HTTP status codes. Global handlers ensure no stack traces leak to clients in production. Validation errors include field-level `details`.

### 7. Structured Logging

- **API:** `structlog` with JSON output in production, console in development
- **Web:** JSON-serialized log lines with service name and timestamp
- **Middleware:** `X-Request-ID` on every request for correlation

### 8. Feature Modules

Each domain (health, future: auth, copy-engine, risk) is a self-contained module with router, service, and schemas. Shared infrastructure stays in `core/`.

### 9. Celery Foundation

Celery is configured with JSON serialization, UTC timezone, and task routing. A `ping` task verifies worker health. `CELERY_TASK_ALWAYS_EAGER=true` in tests runs tasks synchronously.

### 10. Database Migrations

Alembic manages schema evolution. Initial migration establishes the versioning baseline. Feature migrations add domain tables incrementally.

### 11. Docker Production Patterns

- Multi-stage builds for minimal images
- Non-root users (`tradeflow`, `nextjs`)
- HEALTHCHECK on API liveness endpoint
- Compose health-gated service dependencies

### 12. CI Pipeline

Three parallel jobs: TypeScript lint/build, Python lint/test with service containers, Docker image build. PRs cannot merge with failing checks.

---

## Environment Variables

Copy `.env.example` to `.env`. Key variables:

| Variable | Description |
|----------|-------------|
| `API_SECRET_KEY` | Min 32 chars — required |
| `DATABASE_URL` | Async PostgreSQL URL (asyncpg) |
| `DATABASE_URL_SYNC` | Sync URL for Alembic (psycopg) |
| `REDIS_URL` | Redis connection |
| `CELERY_BROKER_URL` | Celery message broker |
| `NEXT_PUBLIC_API_URL` | Web → API base URL |

---

## Git Hooks

Husky runs lint-staged on pre-commit:
- TypeScript: ESLint + Prettier
- Python: Ruff check + format

---

## License

Proprietary — All rights reserved.
