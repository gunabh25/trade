# Railway Setup Guide

Step-by-step instructions to deploy TradeFlow AI on Railway.

---

## 1. Prerequisites

- Railway account ([railway.app](https://railway.app))
- GitHub repository connected
- Railway CLI (optional): `npm install -g @railway/cli`

---

## 2. Create Project

1. Railway Dashboard → **New Project** → **Deploy from GitHub repo**
2. Select the `trade` repository
3. Do **not** deploy the default service yet — we'll configure manually

---

## 3. Add Data Stores

### PostgreSQL

1. **+ New** → **Database** → **PostgreSQL**
2. Name: `tradeflow-postgres`
3. Note the `DATABASE_URL` variable (Railway exposes `${{Postgres.DATABASE_URL}}`)

### Redis

1. **+ New** → **Database** → **Redis**
2. Name: `tradeflow-redis`
3. Note `${{Redis.REDIS_URL}}`

---

## 4. Create Application Services

### 4.1 API — `tradeflow-api`

| Setting        | Value                  |
| -------------- | ---------------------- |
| Source         | GitHub repo            |
| Root directory | `/` (repo root)        |
| Dockerfile     | `apps/api/Dockerfile`  |
| Config file    | `railway.toml`         |
| Health check   | `/api/v1/health/ready` |

**Variables** (shared with worker/beat via Railway variable groups):

```bash
APP_ENV=production
DATABASE_URL=${{Postgres.DATABASE_URL}}
DATABASE_URL_SYNC=${{Postgres.DATABASE_URL}}
REDIS_URL=${{Redis.REDIS_URL}}
CELERY_BROKER_URL=${{Redis.REDIS_URL}}/1
CELERY_RESULT_BACKEND=${{Redis.REDIS_URL}}/2
API_SECRET_KEY=<openssl rand -hex 32>
API_CORS_ORIGINS=https://<web-domain>
API_TRUSTED_HOSTS=<api-domain>,${{RAILWAY_PUBLIC_DOMAIN}}
FRONTEND_URL=https://<web-domain>
OAUTH_REDIRECT_BASE_URL=https://<api-domain>
```

Generate domain: Settings → Networking → **Generate Domain**

### 4.2 Web — `tradeflow-web`

| Setting      | Value                   |
| ------------ | ----------------------- |
| Dockerfile   | `apps/web/Dockerfile`   |
| Config file  | `apps/web/railway.toml` |
| Health check | `/api/health`           |

**Build variables** (must be set before build):

```bash
NEXT_PUBLIC_APP_URL=https://<web-domain>
NEXT_PUBLIC_API_URL=https://<api-domain>
NEXT_PUBLIC_API_VERSION=v1
```

In Railway: mark these as available at **build time** (Railway → Variables → "Build" toggle).

### 4.3 Celery Worker — `tradeflow-worker`

| Setting       | Value                       |
| ------------- | --------------------------- |
| Dockerfile    | `apps/api/Dockerfile`       |
| Config file   | `infra/railway/worker.toml` |
| Start command | `./scripts/start-worker.sh` |

Copy all API environment variables (same image, same config).

### 4.4 Celery Beat — `tradeflow-beat`

| Setting     | Value                     |
| ----------- | ------------------------- |
| Dockerfile  | `apps/api/Dockerfile`     |
| Config file | `infra/railway/beat.toml` |
| Replicas    | **1 only**                |

---

## 5. Variable Groups (Recommended)

Create a Railway **Shared Variable Group** linked to api, worker, and beat:

- Database URLs
- Redis URLs
- `API_SECRET_KEY`
- Stripe, SMTP, OAuth secrets

---

## 6. Custom Domains

1. API service → Settings → Custom Domain → `api.yourdomain.com`
2. Web service → Custom Domain → `app.yourdomain.com`
3. Update `API_CORS_ORIGINS`, `FRONTEND_URL`, `NEXT_PUBLIC_*`, OAuth redirect URIs
4. Railway provisions HTTPS automatically via Let's Encrypt

---

## 7. First Deploy

```bash
# Option A: Push to main (CI deploys automatically after tests pass)
git push origin main

# Option B: Manual CLI
railway link
railway up --service tradeflow-api
```

Watch deploy logs for:

```
[migrate] Running alembic upgrade head…
[migrate] Database schema is up to date.
[api] Starting uvicorn on 0.0.0.0:XXXX
```

---

## 8. Verify

```bash
curl https://<api-domain>/api/v1/health/ready
curl https://<web-domain>/api/health
```

Register a user, log in, and confirm dashboard loads.

---

## 9. GitHub Actions Deploy

1. Railway → Project Settings → **Tokens** → Create project token
2. GitHub → Repository → Settings → Secrets → `RAILWAY_TOKEN`
3. Push to `main` — CI runs, then `deploy-railway.yml` deploys all services

Manual deploy: Actions → **Deploy to Railway** → **Run workflow**

---

## Architectural Decisions

| Decision                          | Rationale                                                 |
| --------------------------------- | --------------------------------------------------------- |
| Monorepo root as Docker context   | Both Dockerfiles copy `packages/*` workspace deps         |
| `preDeployCommand` for migrations | Schema updated before new code serves traffic; idempotent |
| Separate worker + beat services   | Beat must be singleton; workers scale independently       |
| `$PORT` in start.sh               | Railway dynamic port assignment                           |
| Build-time `NEXT_PUBLIC_*`        | Next.js inlines public env vars at compile time           |
| URL auto-normalization in config  | Railway Postgres plugin uses bare `postgresql://`         |
