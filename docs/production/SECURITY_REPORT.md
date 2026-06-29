# Security Report — Production Hardening

**Date:** June 2026  
**Standard:** OWASP ASVS Level 2 alignment (pragmatic)

## Summary

Security controls were reviewed and hardened across authentication, transport, headers, rate limiting, secrets management, and error reporting. The platform follows defense-in-depth: HttpOnly cookies, CSRF double-submit, bcrypt passwords, Fernet encryption at rest, and Redis-backed brute-force protection.

## OWASP Top 10 Mitigations

| Risk                          | Control                                                    | Status               |
| ----------------------------- | ---------------------------------------------------------- | -------------------- |
| A01 Broken Access Control     | Role-based admin gate, subscription entitlements           | ✅ Existing          |
| A02 Cryptographic Failures    | bcrypt, Fernet, HS256 JWT, TLS at edge (required)          | ✅ + iss/aud in prod |
| A03 Injection                 | SQLAlchemy ORM, parameterized queries, Pydantic validation | ✅ Existing          |
| A04 Insecure Design           | CSRF on mutating auth routes, refresh token rotation       | ✅ Existing          |
| A05 Security Misconfiguration | Security headers middleware, prod disables OpenAPI         | ✅ **New**           |
| A06 Vulnerable Components     | Dependabot/CI, pinned Docker base images                   | ✅ Existing          |
| A07 Auth Failures             | Login lockout (5 attempts / 15 min), auth rate limit       | ✅ Existing          |
| A08 Data Integrity            | Stripe webhook signature verification                      | ✅ Existing          |
| A09 Logging Failures          | structlog JSON, Sentry with credential scrubbing           | ✅ **New**           |
| A10 SSRF                      | No user-controlled URL fetch in core paths                 | ✅ Existing          |

## JWT Review

| Control     | Implementation                                     |
| ----------- | -------------------------------------------------- |
| Algorithm   | HS256 only (explicit allowlist in decode)          |
| Access TTL  | 15 minutes (configurable)                          |
| Refresh TTL | 7 days, stored hashed in DB                        |
| Claims      | `sub`, `exp`, `type`, `sid`, `roles`               |
| Production  | `iss=tradeflow-api`, `aud=tradeflow-web` enforced  |
| Secret      | `API_SECRET_KEY` ≥ 32 chars (validated at startup) |
| Storage     | HttpOnly + Secure cookies in production            |

**Recommendation:** Rotate `API_SECRET_KEY` with a planned maintenance window; invalidate all sessions.

## OAuth Review

| Provider | Flow                           | Notes                                     |
| -------- | ------------------------------ | ----------------------------------------- |
| Google   | Authorization code via authlib | Credentials optional; disabled when unset |
| GitHub   | Authorization code via authlib | Same pattern                              |

Controls:

- OAuth tokens encrypted at rest via `EncryptionService` (Fernet)
- Redirect URI bound to `OAUTH_REDIRECT_BASE_URL`
- State parameter managed by authlib

**Production requirements:**

- Register exact redirect URIs in Google/GitHub consoles
- Use separate OAuth apps for staging vs production
- Set `OAUTH_REDIRECT_BASE_URL=https://api.example.com`

## Rate Limiting

| Layer             | Limit                     | Scope                                 |
| ----------------- | ------------------------- | ------------------------------------- |
| Auth endpoints    | 20/min                    | Per IP (`AUTH_RATE_LIMIT_PER_MINUTE`) |
| Login brute-force | 5 attempts → 900s lockout | Per email (Redis)                     |
| Global API        | 300/min                   | Per IP (`API_RATE_LIMIT_PER_MINUTE`)  |
| Broker adapters   | Token bucket              | Per connection                        |

Exempt from global limit: `/api/v1/health/*`, `/metrics`, OpenAPI docs (disabled in prod).

## Security Headers (New)

Applied on every API response:

```
X-Content-Type-Options: nosniff
X-Frame-Options: DENY
Referrer-Policy: strict-origin-when-cross-origin
X-XSS-Protection: 0
Permissions-Policy: camera=(), microphone=(), geolocation=(), payment=()
Strict-Transport-Security: max-age=31536000; includeSubDomains; preload  (production)
Content-Security-Policy: default-src 'none'; frame-ancestors 'none'  (production API)
```

Web (Next.js): `poweredByHeader: false`, `compress: true`.

## Secrets & Environment Variables

| Secret      | Variable                                     | Notes                             |
| ----------- | -------------------------------------------- | --------------------------------- |
| JWT signing | `API_SECRET_KEY`                             | Never commit; rotate periodically |
| DB password | `POSTGRES_PASSWORD`                          | Required in prod compose overlay  |
| Stripe      | `STRIPE_SECRET_KEY`, `STRIPE_WEBHOOK_SECRET` | Webhook sig verification          |
| OAuth       | `*_OAUTH_CLIENT_SECRET`                      | Per provider                      |
| Sentry      | `SENTRY_DSN`                                 | Optional; scrubbed before send    |
| Grafana     | `GRAFANA_ADMIN_PASSWORD`                     | Required for prod overlay         |

Template: `.env.production.example`

Production auto-enforcement:

- `AUTH_COOKIE_SECURE=true` when `APP_ENV=production`
- `API_LOG_FORMAT=json` forced in production
- OpenAPI/docs disabled in production

## Sentry Error Tracking

When `SENTRY_DSN` is set:

- FastAPI, Starlette, SQLAlchemy, Redis integrations
- `before_send` scrubber removes Authorization, Cookie, CSRF, passwords
- `send_default_pii=false`
- Trace sampling: 10% default (`SENTRY_TRACES_SAMPLE_RATE`)
- Profiling: 10% default (`SENTRY_PROFILES_SAMPLE_RATE`)

## Trusted Hosts

Set `API_TRUSTED_HOSTS=api.example.com,api` in production to enable Starlette `TrustedHostMiddleware` and reject Host header attacks.

## Pre-Production Security Checklist

- [ ] Generate strong `API_SECRET_KEY` (`openssl rand -hex 32`)
- [ ] Set `AUTH_COOKIE_SECURE=true` and `AUTH_COOKIE_DOMAIN`
- [ ] Configure TLS at load balancer (HTTPS only)
- [ ] Restrict Postgres/Redis ports (not exposed in prod compose)
- [ ] Set `API_CORS_ORIGINS` to exact frontend origin(s)
- [ ] Configure `API_TRUSTED_HOSTS`
- [ ] Enable Sentry with production DSN
- [ ] Review admin user accounts and roles
- [ ] Run `alembic upgrade head`
- [ ] Verify Stripe webhook endpoint uses HTTPS + signature verification

## Residual Risks

1. **No WAF** — rely on edge provider or add Cloudflare/AWS WAF
2. **Single Redis instance** — no HA failover in default compose
3. **Web Sentry** — API instrumented; add `@sentry/nextjs` for frontend errors
4. **CSP on web app** — API CSP is restrictive; web app needs its own CSP policy for Next.js assets
