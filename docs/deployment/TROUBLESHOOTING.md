# Troubleshooting Guide — Railway Deployment

---

## API Won't Start

### `API_SECRET_KEY must be at least 32 characters`

Generate a new key:

```bash
openssl rand -hex 32
```

Set as `API_SECRET_KEY` on api, worker, and beat services.

### `connection refused` to PostgreSQL

- Verify Postgres plugin is linked to the API service
- Check `DATABASE_URL=${{Postgres.DATABASE_URL}}` is set
- Ensure API service is in the same Railway project as Postgres

### Port binding errors

Railway injects `$PORT`. Confirm `start.sh` is the start command (not hardcoded `8000`).

---

## Health Check Failing

### `/api/v1/health/ready` returns 503

Check which dependency is unhealthy:

```bash
curl -s https://<api>/api/v1/health/ready | jq '.data.checks'
```

| Check           | Fix                                             |
| --------------- | ----------------------------------------------- |
| `database`      | Verify `DATABASE_URL`, Postgres plugin running  |
| `redis`         | Verify `REDIS_URL`, Redis plugin running        |
| `celery_broker` | Verify `CELERY_BROKER_URL` points to Redis DB 1 |

---

## Web Shows Blank / API Errors

### Client calls `localhost:8000`

`NEXT_PUBLIC_API_URL` was not set at **build time**.

1. Set `NEXT_PUBLIC_API_URL=https://<api-domain>` in Railway web service
2. Enable **Build** variable toggle
3. Trigger redeploy (rebuild required)

### CORS errors in browser

Set `API_CORS_ORIGINS` to exact web origin:

```bash
API_CORS_ORIGINS=https://app.example.com
```

No trailing slash. Redeploy API after change.

### Cookie auth not working

- `AUTH_COOKIE_SECURE=true` requires HTTPS
- `FRONTEND_URL` must match web domain
- For custom domains with subdomains, set `AUTH_COOKIE_DOMAIN=.example.com`
- Cross-origin: ensure CORS allows credentials (already configured in API)

---

## Migrations

### `relation "users" does not exist`

Migrations didn't run:

```bash
railway run --service tradeflow-api ./scripts/migrate.sh
```

Verify `railway.toml` has `preDeployCommand = "./scripts/migrate.sh"`.

### Migration stuck / timeout

Check Alembic logs in deploy output. Long migrations may need increased `healthcheckTimeout` in `railway.toml`.

---

## Celery

### Tasks not executing

1. Verify worker service is running: Railway logs for `tradeflow-worker`
2. Check `CELERY_BROKER_URL` matches Redis URL
3. Confirm queues: `CELERY_QUEUES=default,copy,risk,notifications,celery`

### Scheduled tasks running twice

Two beat instances running. Scale `tradeflow-beat` to **exactly 1 replica**.

### `KeyError: task not registered`

Ensure worker image includes latest `workers/__init__.py` task imports. Redeploy worker after API deploy.

---

## Rate Limiting in Tests / High Traffic

Auth endpoints return `403 Rate limit exceeded`:

- Expected under load testing with default limits
- Increase `AUTH_RATE_LIMIT_PER_MINUTE` for staging
- Redis keys: `ratelimit:register:*`, `ratelimit:login:*`

---

## OAuth

### Redirect URI mismatch

Register exact callback URLs at Google/GitHub:

```
https://<api-domain>/api/v1/auth/oauth/google/callback
https://<api-domain>/api/v1/auth/oauth/github/callback
```

Set `OAUTH_REDIRECT_BASE_URL=https://<api-domain>`.

---

## Stripe Webhooks

### Signature verification failed

- `STRIPE_WEBHOOK_SECRET` must match Stripe dashboard
- Webhook URL: `https://<api-domain>/api/v1/billing/webhook`

---

## Docker Build Failures

### Web build: `NEXT_PUBLIC_API_URL` undefined

Pass build args in Railway or `apps/web/railway.toml` `[build.args]`.

### API build: context error

Docker build context must be **repository root**, not `apps/api`.

---

## CI/CD Deploy

### `deploy-railway.yml` not running

- Requires CI workflow to complete successfully on `main`
- Or trigger manually via **workflow_dispatch**

### `RAILWAY_TOKEN` invalid

Create new token: Railway → Project Settings → Tokens

---

## Logs

```bash
# Railway CLI
railway logs --service tradeflow-api
railway logs --service tradeflow-worker

# Filter errors
railway logs --service tradeflow-api | grep ERROR
```

API uses structured JSON logging in production (`API_LOG_FORMAT=json`).

---

## Getting Help

1. Check [Deployment Readiness](./DEPLOYMENT_READINESS.md)
2. Review [Environment Variables](./ENVIRONMENT_VARIABLES.md)
3. Railway status: [status.railway.app](https://status.railway.app)
