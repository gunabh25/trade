# Environment Variable Guide

Complete reference for TradeFlow AI environment variables.

Templates:

- Local dev: `.env.example`
- Self-hosted prod: `.env.production.example`
- Railway: `.env.railway.example`

---

## Frontend (Next.js / Web Service)

| Variable                  | Required | Build-time | Description                                     |
| ------------------------- | -------- | ---------- | ----------------------------------------------- |
| `NODE_ENV`                | Yes      | Yes        | `production` in Railway                         |
| `NEXT_PUBLIC_APP_URL`     | Yes      | **Yes**    | Public web URL (e.g. `https://app.example.com`) |
| `NEXT_PUBLIC_API_URL`     | Yes      | **Yes**    | Public API URL (e.g. `https://api.example.com`) |
| `NEXT_PUBLIC_API_VERSION` | No       | Yes        | Default: `v1`                                   |
| `NEXT_PUBLIC_SENTRY_DSN`  | No       | Yes        | Client-side Sentry                              |

> **Important:** `NEXT_PUBLIC_*` variables are embedded at `next build`. Changing them requires a **rebuild** of the web service.

---

## Backend (FastAPI / API, Worker, Beat)

### Application

| Variable                        | Required | Default        | Description                               |
| ------------------------------- | -------- | -------------- | ----------------------------------------- |
| `APP_ENV`                       | Yes      | `development`  | `production` enables hardened defaults    |
| `APP_NAME`                      | No       | `TradeFlow AI` | Display name                              |
| `APP_VERSION`                   | No       | `0.1.0`        | Release tag for Sentry/metrics            |
| `PORT`                          | Railway  | —              | Railway-injected; mapped to Uvicorn port  |
| `API_HOST`                      | No       | `0.0.0.0`      | Bind address                              |
| `API_PORT`                      | No       | `8000`         | Fallback if `PORT` unset                  |
| `API_WORKERS`                   | No       | `1`            | Uvicorn worker processes                  |
| `API_GRACEFUL_SHUTDOWN_SECONDS` | No       | `30`           | Drain timeout                             |
| `RUN_MIGRATIONS_ON_START`       | No       | `false`        | Use `preDeployCommand` instead on Railway |

### Security

| Variable                          | Required   | Description                           |
| --------------------------------- | ---------- | ------------------------------------- |
| `API_SECRET_KEY`                  | **Yes**    | JWT signing key, min 32 chars         |
| `API_CORS_ORIGINS`                | Yes (prod) | Comma-separated allowed origins       |
| `API_TRUSTED_HOSTS`               | Yes (prod) | Comma-separated Host header allowlist |
| `API_RATE_LIMIT_PER_MINUTE`       | No         | Global API rate limit (default 300)   |
| `AUTH_RATE_LIMIT_PER_MINUTE`      | No         | Auth endpoint limit (default 20)      |
| `JWT_ISSUER`                      | Prod       | Token issuer claim                    |
| `JWT_AUDIENCE`                    | Prod       | Token audience claim                  |
| `JWT_ACCESS_TOKEN_EXPIRE_MINUTES` | No         | Default 15                            |
| `JWT_REFRESH_TOKEN_EXPIRE_DAYS`   | No         | Default 7                             |

### Cookies

| Variable                  | Prod value | Description                        |
| ------------------------- | ---------- | ---------------------------------- |
| `AUTH_COOKIE_SECURE`      | `true`     | HTTPS-only cookies                 |
| `AUTH_COOKIE_SAMESITE`    | `lax`      | CSRF mitigation                    |
| `AUTH_COOKIE_DOMAIN`      | Optional   | e.g. `.example.com` for subdomains |
| `FRONTEND_URL`            | Web URL    | Redirect target after OAuth        |
| `OAUTH_REDIRECT_BASE_URL` | API URL    | OAuth callback base                |

---

## Database (PostgreSQL)

| Variable                | Required | Description                                       |
| ----------------------- | -------- | ------------------------------------------------- |
| `DATABASE_URL`          | **Yes**  | Async SQLAlchemy URL (`postgresql+asyncpg://...`) |
| `DATABASE_URL_SYNC`     | **Yes**  | Sync URL for Alembic (`postgresql+psycopg://...`) |
| `DATABASE_POOL_SIZE`    | No       | Default 10                                        |
| `DATABASE_MAX_OVERFLOW` | No       | Default 20                                        |
| `DATABASE_POOL_TIMEOUT` | No       | Default 30 seconds                                |

**Railway:** Reference `${{Postgres.DATABASE_URL}}` — the app auto-converts `postgresql://` to the correct driver.

---

## Redis

| Variable                   | Required | Description                            |
| -------------------------- | -------- | -------------------------------------- |
| `REDIS_URL`                | **Yes**  | General Redis (DB 0)                   |
| `REDIS_MAX_CONNECTIONS`    | No       | Pool size (default 50)                 |
| `CELERY_BROKER_URL`        | **Yes**  | Celery message broker (recommend `/1`) |
| `CELERY_RESULT_BACKEND`    | **Yes**  | Task results (recommend `/2`)          |
| `CELERY_TASK_ALWAYS_EAGER` | No       | `true` for sync testing only           |

---

## OAuth

| Variable                     | Description               |
| ---------------------------- | ------------------------- |
| `GOOGLE_OAUTH_CLIENT_ID`     | Google Cloud OAuth client |
| `GOOGLE_OAUTH_CLIENT_SECRET` | Google secret             |
| `GITHUB_OAUTH_CLIENT_ID`     | GitHub OAuth app          |
| `GITHUB_OAUTH_CLIENT_SECRET` | GitHub secret             |

Redirect URIs to register:

- Google: `https://<api-domain>/api/v1/auth/oauth/google/callback`
- GitHub: `https://<api-domain>/api/v1/auth/oauth/github/callback`

---

## Stripe (Billing)

| Variable                 | Description            |
| ------------------------ | ---------------------- |
| `STRIPE_SECRET_KEY`      | Server-side API key    |
| `STRIPE_PUBLISHABLE_KEY` | Client-side key        |
| `STRIPE_WEBHOOK_SECRET`  | Webhook signing secret |
| `STRIPE_TAX_ENABLED`     | Enable Stripe Tax      |

Webhook URL: `https://<api-domain>/api/v1/billing/webhook`

---

## Email (SMTP)

| Variable          | Description   |
| ----------------- | ------------- |
| `SMTP_HOST`       | SMTP server   |
| `SMTP_PORT`       | Default 587   |
| `SMTP_USER`       | Auth username |
| `SMTP_PASSWORD`   | Auth password |
| `SMTP_FROM_EMAIL` | From address  |

When unset in development, emails are logged to stdout.

---

## Broker / Trading (Optional Platform Keys)

User broker credentials are stored encrypted per-connection in the database. Platform-level vars:

| Variable                               | Default | Description                 |
| -------------------------------------- | ------- | --------------------------- |
| `BROKER_RETRY_MAX_ATTEMPTS`            | 3       | Adapter retry count         |
| `BROKER_HEALTH_CHECK_INTERVAL_SECONDS` | 30      | Health poll interval        |
| `COPY_RETRY_MAX_ATTEMPTS`              | 5       | Copy engine retries         |
| `COPY_MAX_PARALLEL_FOLLOWERS`          | 10      | Parallel follower execution |
| `RISK_MONITOR_INTERVAL_SECONDS`        | 30      | Risk poll interval          |

---

## Celery Worker

| Variable             | Default                                | Description          |
| -------------------- | -------------------------------------- | -------------------- |
| `CELERY_CONCURRENCY` | 4                                      | Worker process count |
| `CELERY_LOG_LEVEL`   | INFO                                   | Log verbosity        |
| `CELERY_QUEUES`      | default,copy,risk,notifications,celery | Subscribed queues    |

---

## Observability

| Variable                    | Description                 |
| --------------------------- | --------------------------- |
| `PROMETHEUS_ENABLED`        | Expose `/metrics` endpoint  |
| `SENTRY_DSN`                | Sentry error tracking       |
| `SENTRY_ENVIRONMENT`        | e.g. `production`           |
| `SENTRY_TRACES_SAMPLE_RATE` | 0.0–1.0                     |
| `API_LOG_LEVEL`             | DEBUG, INFO, WARNING, ERROR |
| `API_LOG_FORMAT`            | `json` (prod) or `console`  |

---

## Uploads

| Variable             | Default           | Notes                |
| -------------------- | ----------------- | -------------------- |
| `AVATAR_UPLOAD_DIR`  | `uploads/avatars` | Ephemeral on Railway |
| `AVATAR_MAX_BYTES`   | 2097152           | 2 MB                 |
| `JOURNAL_UPLOAD_DIR` | `uploads/journal` | Ephemeral on Railway |
| `JOURNAL_MAX_BYTES`  | 5242880           | 5 MB                 |

---

## GitHub Actions Secrets

| Secret          | Description                  |
| --------------- | ---------------------------- |
| `RAILWAY_TOKEN` | Railway project deploy token |
