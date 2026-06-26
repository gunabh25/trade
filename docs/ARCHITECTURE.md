# TradeFlow AI — Foundation Architecture

This document describes the architectural decisions for the TradeFlow AI monorepo foundation.

## Monorepo Layout

```
apps/web     → Next.js 15 dashboard (TypeScript)
apps/api     → FastAPI backend (Python)
packages/ui  → Shared shadcn/ui component library
packages/types → Shared API contract types
packages/config → ESLint + TypeScript configs
```

**Decision:** Hybrid TypeScript + Python monorepo. The frontend and shared UI/types use pnpm workspaces; the API is an independent Python package. This matches team boundaries (UI engineers vs. backend engineers) while keeping contracts aligned via `@tradeflow/types`.

## Backend: FastAPI over Node/Fastify

**Decision:** Python FastAPI for the API layer.

**Rationale:**

- Celery is the mature standard for distributed task queues in Python — critical for future copy engine workers, reconciliation, and alerts.
- SQLAlchemy 2 + Alembic provides battle-tested ORM and migrations for financial audit data.
- FastAPI generates OpenAPI/Swagger automatically with Pydantic v2 validation.
- Async SQLAlchemy + asyncpg supports high-concurrency I/O without blocking the event loop.

## Frontend: Next.js 15 + React 19

**Decision:** Next.js App Router with React Server Components for the dashboard.

**Rationale:**

- Server Components reduce client bundle size for read-heavy dashboard pages.
- Built-in routing, metadata, and production optimizations.
- `standalone` output enables minimal Docker images.

## Feature-Based Architecture

Both `apps/web` and `apps/api` use **feature modules** rather than layer-only folders:

```
features/health/
  api/          → data fetching (web) or router (api)
  components/   → UI (web)
  service.py    → business logic (api)
  schemas.py    → Pydantic models (api)
```

**Decision:** Colocate by feature domain, not by file type globally.

**Rationale:** Features like copy-engine, risk, and billing can evolve independently. Teams can own vertical slices. Shared infrastructure lives in `core/` (api) and `lib/` (web).

## Dependency Injection

**Decision:** `dependency-injector` container in FastAPI; FastAPI `Depends()` at the route boundary.

**Rationale:**

- Services (`HealthService`) receive dependencies explicitly — testable without HTTP.
- Container manages singletons (DB engine, Redis) with correct lifecycle.
- Wiring is declarative; new features register providers without modifying global state.

## API Versioning

**Decision:** URL path versioning — `/api/v1/*`.

**Rationale:**

- Explicit and cache-friendly.
- OpenAPI docs scoped per version.
- v2 can run alongside v1 during migrations.

All responses use a standard envelope:

```json
{ "data": { ... }, "meta": { "requestId": "..." } }
```

Errors use a parallel envelope:

```json
{ "error": { "code": "...", "message": "...", "requestId": "..." } }
```

## Centralized Error Handling

**Decision:** `AppError` hierarchy + FastAPI exception handlers in `core/exception_handlers.py`.

**Rationale:**

- Consistent error shape across all endpoints.
- Structured logging on every error with `request_id`.
- Validation errors mapped to `VALIDATION_ERROR` with field-level details.

## Logging

**Decision:** `structlog` (API) and JSON `logger` (web).

**Rationale:**

- Structured JSON logs aggregate in CloudWatch/Datadog/Grafana without regex parsing.
- `request_id` bound via middleware for distributed tracing correlation.
- Log level configurable via `API_LOG_LEVEL`.

## Database

**Decision:** PostgreSQL 16 + SQLAlchemy 2 async + Alembic migrations.

**Rationale:**

- ACID compliance for audit logs and billing state.
- Async engine for FastAPI concurrency.
- Sync URL separate for Alembic (Alembic doesn't run async migrations natively).

## Redis + Celery

**Decision:** Redis for cache/pub-sub; Celery for background jobs.

**Rationale:**

- Celery provides retry, visibility timeout, and worker scaling out of the box.
- Separate Redis DB indexes for broker (1) and result backend (2) avoid key collisions.
- Foundation includes a `ping` task to verify worker connectivity.

## Shared Packages

| Package             | Purpose                                                 |
| ------------------- | ------------------------------------------------------- |
| `@tradeflow/types`  | API contract types shared between web and documentation |
| `@tradeflow/ui`     | shadcn/ui components with Tailwind design tokens        |
| `@tradeflow/config` | ESLint + TypeScript shared configs                      |

## Docker

**Decision:** Multi-stage Dockerfiles; `docker compose` for local full stack.

**Rationale:**

- API image: slim Python 3.12, non-root user, healthcheck on liveness endpoint.
- Web image: Next.js standalone output, non-root `nextjs` user.
- Compose wires postgres, redis, api, celery-worker, web with health-gated dependencies.

## CI/CD

**Decision:** GitHub Actions with three jobs — TypeScript, Python, Docker.

**Rationale:**

- Parallel feedback on PRs.
- Python job runs against real Postgres + Redis service containers.
- Docker build gated on lint/test pass.

## Security Foundation

- Session-ready auth structure (Lucia/FastAPI sessions in future feature phase).
- `API_SECRET_KEY` minimum 32 characters enforced at settings load.
- CORS restricted to configured origins.
- Non-root container users.
- No secrets in repository — `.env.example` only.

## What Is Not Built Yet

Per foundation scope, the following are intentionally deferred:

- User authentication and authorization
- Trade copy engine
- Broker integrations (Tradovate, Rithmic)
- Billing (Stripe)
- Domain database tables

The foundation provides health checks, OpenAPI docs, DI, logging, errors, migrations scaffold, Celery, and CI/CD to build features on.
