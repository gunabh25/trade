# Deployment Readiness Report — Railway

**Generated:** 2026-06-29  
**Platform:** [Railway](https://railway.app)  
**Project:** TradeFlow AI (monorepo)

---

## Executive Summary

TradeFlow AI is **ready for Railway deployment** after the changes in this branch. The stack requires **6 Railway services** (Postgres plugin, Redis plugin, API, Web, Celery worker, Celery beat) plus GitHub Actions for CI/CD.

---

## Architecture on Railway

```
                    ┌─────────────────┐
                    │  tradeflow-web  │  Next.js 15 (standalone)
                    │  :PORT / HTTPS  │
                    └────────┬────────┘
                             │ NEXT_PUBLIC_API_URL
                    ┌────────▼────────┐
                    │ tradeflow-api   │  FastAPI + Uvicorn
                    │ preDeploy:      │  alembic upgrade head
                    │ migrate.sh      │
                    └────────┬────────┘
              ┌──────────────┼──────────────┐
              │              │              │
     ┌────────▼────┐  ┌──────▼──────┐  ┌───▼────────────┐
     │  PostgreSQL │  │    Redis    │  │ tradeflow-worker│
     │   (plugin)  │  │   (plugin)  │  │ + tradeflow-beat│
     └─────────────┘  └─────────────┘  └─────────────────┘
```

---

## Issues Found & Resolved

| Issue                               | Severity | Resolution                                                            |
| ----------------------------------- | -------- | --------------------------------------------------------------------- |
| No `railway.toml`                   | Blocker  | Added `railway.toml`, `apps/web/railway.toml`, `infra/railway/*.toml` |
| API ignored Railway `$PORT`         | Blocker  | `start.sh` uses `PORT` → `API_PORT` → 8000                            |
| Migrations not run on deploy        | Blocker  | `preDeployCommand = ./scripts/migrate.sh`                             |
| `NEXT_PUBLIC_*` not at Docker build | Blocker  | Web Dockerfile accepts build args                                     |
| Railway `postgresql://` URL format  | High     | `config.py` normalizes to asyncpg/psycopg                             |
| Celery beat tasks not registered    | High     | Import `notification_tasks`, `billing_tasks`                          |
| No deploy CI workflow               | Medium   | `.github/workflows/deploy-railway.yml`                                |
| Ephemeral upload dirs               | Medium   | Documented; recommend S3 for prod                                     |
| Prometheus/Grafana in compose       | Info     | Not deployed on Railway (use Sentry)                                  |

---

## Service Matrix

| Service          | Dockerfile            | Config                      | Start             | Health                 |
| ---------------- | --------------------- | --------------------------- | ----------------- | ---------------------- |
| tradeflow-api    | `apps/api/Dockerfile` | `railway.toml`              | `start.sh`        | `/api/v1/health/ready` |
| tradeflow-web    | `apps/web/Dockerfile` | `apps/web/railway.toml`     | `node server.js`  | `/api/health`          |
| tradeflow-worker | `apps/api/Dockerfile` | `infra/railway/worker.toml` | `start-worker.sh` | —                      |
| tradeflow-beat   | `apps/api/Dockerfile` | `infra/railway/beat.toml`   | `start-beat.sh`   | —                      |
| PostgreSQL       | Railway plugin        | —                           | managed           | —                      |
| Redis            | Railway plugin        | —                           | managed           | —                      |

---

## Required Secrets (GitHub)

| Secret          | Purpose                                     |
| --------------- | ------------------------------------------- |
| `RAILWAY_TOKEN` | Project deploy token from Railway dashboard |

---

## Pre-Deploy Checklist

- [ ] Create Railway project and link GitHub repo
- [ ] Add Postgres + Redis plugins
- [ ] Create 4 application services with correct Dockerfile paths
- [ ] Set variables from `.env.railway.example`
- [ ] Generate `API_SECRET_KEY` (32+ chars)
- [ ] Configure custom domains + HTTPS (Railway automatic)
- [ ] Set OAuth redirect URLs to production API domain
- [ ] Configure Stripe webhook URL
- [ ] Add `RAILWAY_TOKEN` to GitHub secrets
- [ ] Run `pnpm test:api:full` locally before first deploy

---

## Known Limitations

1. **File uploads** (avatars, journal screenshots) use local disk — ephemeral on Railway restarts. Use object storage for production persistence.
2. **Celery beat** must run exactly **one replica** to avoid duplicate scheduled jobs.
3. **WebSocket** connections require Railway's HTTP/1.1 upgrade support on the API service public domain.
4. **Multi-worker Uvicorn** (`API_WORKERS>1`) disables in-process WebSocket state sharing — use `API_WORKERS=1` if WebSocket fan-out is critical, or add Redis pub/sub.

---

## Related Documentation

- [Railway Setup Guide](./RAILWAY_SETUP.md)
- [Environment Variables](./ENVIRONMENT_VARIABLES.md)
- [Deployment Guide](./DEPLOYMENT_GUIDE.md)
- [Rollback Guide](./ROLLBACK.md)
- [Troubleshooting](./TROUBLESHOOTING.md)
