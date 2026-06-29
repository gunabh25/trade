# Deployment Guide

Production deployment guide for TradeFlow AI.

---

## Deployment Targets

| Target             | Use case                 | Config                                           |
| ------------------ | ------------------------ | ------------------------------------------------ |
| **Railway**        | Recommended SaaS hosting | `railway.toml`, `.env.railway.example`           |
| **Docker Compose** | Self-hosted VPS          | `docker-compose.yml` + `docker-compose.prod.yml` |

This guide covers both; Railway is the primary path.

---

## Railway Deployment (Recommended)

### Quick start

```bash
# 1. Local validation
docker compose up -d postgres redis
pnpm test:api:full
pnpm build

# 2. Configure Railway (see RAILWAY_SETUP.md)

# 3. Deploy
git push origin main   # CI → deploy-railway.yml
```

### What happens on deploy

1. **GitHub CI** runs lint, tests, Docker builds
2. **Deploy workflow** triggers Railway redeploy for each service
3. **API preDeploy** runs `alembic upgrade head` (migrations)
4. **API** starts Uvicorn with `$PORT`, proxy headers, graceful shutdown
5. **Worker/Beat** connect to Redis broker
6. **Web** serves Next.js standalone on `$PORT`

### Health verification

```bash
curl -fsS https://api.example.com/api/v1/health/ready | jq
curl -fsS https://app.example.com/api/health | jq
```

Expected API readiness:

```json
{
  "data": {
    "status": "healthy",
    "checks": {
      "database": { "status": "healthy" },
      "redis": { "status": "healthy" },
      "celery_broker": { "status": "healthy" }
    }
  }
}
```

---

## Self-Hosted (Docker Compose)

```bash
cp .env.production.example .env
# Edit .env with production values

docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d

docker compose exec api alembic upgrade head
```

---

## Database Migrations

### Strategy

| Environment | Method                                                                            |
| ----------- | --------------------------------------------------------------------------------- |
| Railway     | `preDeployCommand: ./scripts/migrate.sh` in `railway.toml`                        |
| Compose     | Manual or `docker compose run api alembic upgrade head`                           |
| Emergency   | Railway one-off shell: `railway run --service tradeflow-api ./scripts/migrate.sh` |

Migrations are **forward-only** in production. Alembic versions live in `apps/api/alembic/versions/`.

### Connection pooling

Configured via environment:

```bash
DATABASE_POOL_SIZE=10        # persistent connections per worker
DATABASE_MAX_OVERFLOW=20     # burst capacity
DATABASE_POOL_TIMEOUT=30     # seconds to wait for connection
```

Railway Postgres connection limits vary by plan — keep `API_WORKERS × (POOL_SIZE + OVERFLOW)` under the limit.

---

## Redis

Used for:

- Session/rate-limit storage
- Celery broker (DB 1) and result backend (DB 2)
- Copy engine retry queue
- Risk monitor state

Configuration:

```bash
REDIS_URL=redis://...
REDIS_MAX_CONNECTIONS=50
CELERY_BROKER_URL=redis://.../1
CELERY_RESULT_BACKEND=redis://.../2
```

Celery is configured with `broker_connection_retry_on_startup=True` for Railway Redis restarts.

---

## Celery

| Component | Service            | Replicas                    |
| --------- | ------------------ | --------------------------- |
| Worker    | `tradeflow-worker` | 1+ (scale with queue depth) |
| Beat      | `tradeflow-beat`   | **1 only**                  |

Queues: `default`, `copy`, `risk`, `notifications`, `celery`

Monitor worker logs in Railway for task execution:

```
[celery-worker] Starting worker (concurrency=4, queues=...)
```

---

## Security Checklist

- [ ] `API_SECRET_KEY` ≥ 32 characters, randomly generated
- [ ] `APP_ENV=production` (enables secure cookies, JSON logs, disables Swagger)
- [ ] `AUTH_COOKIE_SECURE=true`
- [ ] `API_CORS_ORIGINS` set to exact web origin(s)
- [ ] `API_TRUSTED_HOSTS` includes API hostname
- [ ] HTTPS enforced (Railway default)
- [ ] Stripe webhook secret configured
- [ ] OAuth redirect URIs whitelisted at providers
- [ ] Sentry DSN configured for error tracking

---

## Monitoring

| Tool          | Endpoint               | Railway               |
| ------------- | ---------------------- | --------------------- |
| API liveness  | `/api/v1/health/live`  | Health check          |
| API readiness | `/api/v1/health/ready` | Primary health check  |
| Web health    | `/api/health`          | Health check          |
| Prometheus    | `/metrics`             | Optional (if enabled) |
| Sentry        | SDK                    | Recommended for prod  |

---

## Related Guides

- [Railway Setup](./RAILWAY_SETUP.md)
- [Environment Variables](./ENVIRONMENT_VARIABLES.md)
- [Rollback](./ROLLBACK.md)
- [Troubleshooting](./TROUBLESHOOTING.md)
