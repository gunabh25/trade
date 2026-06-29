# Rollback Guide

Procedures for rolling back TradeFlow AI deployments on Railway.

---

## When to Rollback

- Health checks failing after deploy
- Elevated 5xx error rate in Sentry
- Database migration caused data issues
- Critical regression in auth, billing, or copy engine

---

## Railway Rollback (Fastest)

### Option 1: Railway Dashboard

1. Open the affected service (usually `tradeflow-api` or `tradeflow-web`)
2. **Deployments** tab
3. Find the last known-good deployment
4. Click **⋯** → **Rollback to this deployment**

Repeat for each service if the release touched multiple images.

### Option 2: Railway CLI

```bash
railway link
railway deployment list --service tradeflow-api
railway deployment rollback <deployment-id> --service tradeflow-api
```

### Option 3: Git Revert + Redeploy

```bash
git revert HEAD
git push origin main
# CI runs tests, deploy workflow redeploys
```

---

## Database Migration Rollback

Alembic migrations in production should be **forward-only**. To reverse a bad migration:

```bash
# One-off Railway shell on API service
railway run --service tradeflow-api alembic downgrade -1

# Or locally against production DB (use with extreme caution)
DATABASE_URL_SYNC=<prod-url> alembic downgrade -1
```

**Before downgrading:**

1. Take a Postgres backup (Railway → Postgres → Backups)
2. Verify no code depends on the new schema
3. Roll back the API service to a version compatible with the older schema

---

## Partial Rollback (API only)

If only the API regressed but web is fine:

1. Rollback `tradeflow-api` only
2. Keep worker/beat on current version **only if** schema is backward compatible
3. If migration ran, worker may need rollback too

---

## Celery Considerations

- **Beat rollback:** Ensure only one beat instance runs the old schedule
- **Worker rollback:** Drain in-flight tasks before rollback (Railway drainingSeconds=30 handles this)
- **Task schema changes:** Old workers may fail on new message formats — rollback worker with API

---

## Verification After Rollback

```bash
curl -fsS https://<api>/api/v1/health/ready
curl -fsS https://<web>/api/health

# Smoke test
curl -X POST https://<api>/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"...","password":"..."}'
```

Check Sentry for new errors in the 15 minutes after rollback.

---

## Prevention

- CI must pass before deploy (`deploy-railway.yml` waits for CI success)
- Use Railway **PR environments** for staging validation
- Run `pnpm test:api:full` before merging to main
- Review Alembic migrations in PR review
