# Architecture Review — Production Readiness

**Date:** June 2026  
**Scope:** TradeFlow AI monorepo (FastAPI API, Next.js web, Celery, PostgreSQL, Redis)

## Executive Summary

TradeFlow AI is a well-structured monorepo with clear domain boundaries, dependency injection, structured logging, and comprehensive database indexing. This review hardens the platform for production with security middleware, observability (Prometheus + Sentry), graceful shutdown, Docker production overlays, and operational documentation.

## System Topology

```
                    ┌─────────────┐
                    │   Next.js   │  :3000  (web)
                    │   (web)     │
                    └──────┬──────┘
                           │ HTTPS / REST
                    ┌──────▼──────┐
                    │   FastAPI   │  :8000  (api)
                    │   + Uvicorn │
                    └─┬─────┬───┬─┘
                      │     │   │
           ┌──────────┘     │   └──────────┐
           ▼                ▼              ▼
    ┌────────────┐   ┌────────────┐  ┌────────────┐
    │ PostgreSQL │   │   Redis    │  │   Celery   │
    │  (primary) │   │ DB0 app    │  │ worker/beat│
    └────────────┘   │ DB1 broker │  └────────────┘
                     │ DB2 results│
                     └────────────┘

    Observability: Prometheus (:9090) → Grafana (:3001)
                   Sentry (external, optional)
```

## Layer Architecture

| Layer        | Technology                            | Production Status                               |
| ------------ | ------------------------------------- | ----------------------------------------------- |
| Presentation | Next.js 15 standalone                 | ✅ compress, health probe, no powered-by header |
| API          | FastAPI + Uvicorn (multi-worker)      | ✅ middleware stack hardened                    |
| Auth         | JWT + HttpOnly cookies + CSRF + OAuth | ✅ iss/aud in production                        |
| Data         | PostgreSQL 16 + SQLAlchemy async      | ✅ pool tuning, migration indexes               |
| Cache/Queue  | Redis 7 + Celery                      | ✅ connection pool, LRU policy in prod          |
| Brokers      | WebSocket adapters + session manager  | ✅ graceful disconnect on shutdown              |
| Billing      | Stripe webhooks                       | ✅ existing                                     |
| Admin        | Enterprise portal                     | ✅ existing                                     |

## Request Pipeline (API)

Middleware order (outer → inner):

1. **TrustedHostMiddleware** — production host allowlist
2. **GZipMiddleware** — response compression (≥1 KB)
3. **SecurityHeadersMiddleware** — OWASP headers, HSTS in production
4. **PrometheusMiddleware** — latency histograms, request counters
5. **GlobalRateLimitMiddleware** — 300 req/min/IP (configurable)
6. **CORSMiddleware** — origin allowlist with credentials
7. **RequestContextMiddleware** — correlation ID + structured logs

## Domain Modules

```
tradeflow/
├── core/           # config, DI, middleware, observability, security
├── features/       # auth, billing, broker, copy, risk, journal, admin...
├── integrations/   # Stripe, broker adapters
├── engine/         # copy orchestrator, retry queue
├── workers/        # Celery tasks
└── notifications/  # multi-channel dispatcher
```

## Key Production Decisions

| Decision                                  | Rationale                                             |
| ----------------------------------------- | ----------------------------------------------------- |
| Multi-worker Uvicorn via `start.sh`       | Utilize CPU; configurable `API_WORKERS`               |
| Readiness probe on `/api/v1/health/ready` | K8s/Docker won't route until DB+Redis+Celery OK       |
| Prometheus at `/metrics`                  | Standard scrape target; Grafana dashboards included   |
| Sentry optional via `SENTRY_DSN`          | Error tracking without forcing vendor lock-in locally |
| JWT iss/aud enforced in production        | Prevents token misuse across services                 |
| Redis DB separation (0/1/2)               | Isolates app cache from Celery broker/results         |
| `.dockerignore`                           | Smaller, faster, more secure image builds             |

## Deployment Model

```bash
# Development
docker compose up --build

# Production overlay (Prometheus + Grafana + hardened env)
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

Pre-deploy checklist:

1. Copy `.env.production.example` → `.env` and fill secrets
2. `alembic upgrade head` (includes `013_production_indexes`)
3. Set `API_SECRET_KEY` ≥ 32 chars (`openssl rand -hex 32`)
4. Configure `SENTRY_DSN`, `STRIPE_*`, OAuth credentials
5. Point DNS + TLS termination (nginx/ALB/Cloudflare)
6. Verify `/api/v1/health/ready` and `/metrics`

## Remaining Recommendations (Post-Launch)

| Priority | Item                                                     |
| -------- | -------------------------------------------------------- |
| P1       | TLS termination at load balancer with cert auto-renewal  |
| P1       | PostgreSQL managed service with automated backups        |
| P2       | Redis Sentinel or ElastiCache for HA                     |
| P2       | `@sentry/nextjs` on web tier for full-stack traces       |
| P2       | OpenTelemetry exporter for distributed tracing           |
| P3       | WAF / DDoS protection at edge                            |
| P3       | Secrets manager (AWS SM / Vault) instead of `.env` files |

## Files Changed for Production

- `apps/api/src/tradeflow/core/app_factory.py` — middleware, shutdown, Sentry
- `apps/api/src/tradeflow/core/observability/` — Prometheus + Sentry
- `apps/api/src/tradeflow/core/security_middleware.py` — OWASP headers
- `apps/api/src/tradeflow/core/rate_limit_middleware.py` — global rate limit
- `apps/api/scripts/start.sh` — multi-worker + graceful shutdown
- `docker-compose.prod.yml` — production overlay
- `infra/prometheus/`, `infra/grafana/` — monitoring stack
- `013_production_indexes.py` — query performance indexes
