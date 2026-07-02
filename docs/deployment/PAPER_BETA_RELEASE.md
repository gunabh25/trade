# Paper Beta Release Checklist

Use this checklist before inviting external beta users.

## 1. Code & CI

- [ ] `main` branch is green in GitHub Actions (lint, typecheck, tests, build)
- [ ] `pytest` passes locally: `./scripts/test-api.sh`
- [ ] Web tests pass: `pnpm test` (from repo root)

## 2. Railway deployment

- [ ] Postgres + Redis plugins attached
- [ ] Services running: **api**, **web**, **worker**, **beat**
- [ ] `API_SECRET_KEY` set (32+ chars, unique)
- [ ] `API_CORS_ORIGINS` includes web public URL
- [ ] `FRONTEND_URL` and `API_PROXY_URL` / `NEXT_PUBLIC_API_URL` set correctly
- [ ] Migrations applied (`alembic upgrade head` via preDeploy)
- [ ] `SENTRY_DSN` set for API (recommended)

## 3. Automated smoke test

```bash
chmod +x scripts/smoke-production.sh
./scripts/smoke-production.sh
```

## 4. Manual production validation

- [ ] Register with terms acceptance
- [ ] Login / logout / session refresh
- [ ] Connect **two** paper broker accounts (leader + follower)
- [ ] Create copy group → add follower → **start copying**
- [ ] Simulate leader event OR place leader order → follower replicates
- [ ] Risk rule CRUD + kill switch activate/deactivate
- [ ] Analytics overview shows data after copy activity
- [ ] Profile save (+ avatar if configured)
- [ ] Admin overview / health pages (admin user)

## 5. Legal & user communication

- [ ] `/terms`, `/privacy`, `/risk-disclosure` pages live
- [ ] Register page requires terms acceptance
- [ ] Beta banner visible in dashboard (paper beta notice)
- [ ] `/help` FAQ shared with beta users
- [ ] `/status` page reachable

## 6. Known limitations (communicate to beta users)

- Paper trading recommended; live broker use at own risk
- Avatars ephemeral on Railway without S3
- Email requires SMTP configuration
- AI defaults to mock without API keys

## 7. Ops

- [ ] At least one user has `ADMIN` role
- [ ] Monitor Celery worker logs during copy events
- [ ] Invite-only access (no public marketing until full launch)

## 8. Post-beta (not required for paper beta)

- [ ] S3 for avatar/journal uploads
- [ ] SMTP for transactional email
- [ ] Copy-trading load tests
- [ ] Tradovate production credentials
- [ ] Stripe live mode
- [ ] Public status vendor (optional upgrade from `/status`)
