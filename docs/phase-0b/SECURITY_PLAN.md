# Security Plan
## Relay — Security Architecture & Controls

**Version:** 1.0  
**Date:** June 26, 2026  
**Phase:** 0B  
**Classification:** Internal

---

## 1. Security Objectives

| Objective | Target |
|-----------|--------|
| Protect broker credentials | Zero plaintext storage; KMS-wrapped encryption |
| Protect user data | Encryption in transit + at rest; access control |
| Ensure copy integrity | Audit log tamper-resistant; idempotent processing |
| Maintain availability | No single credential compromise affects all users |
| Compliance readiness | GDPR/CCPA baseline; SOC 2 Type I path by Month 12 |

---

## 2. Threat Model

### 2.1 Assets
1. **Broker credentials** (Tradovate username/password or API tokens) — **Critical**
2. **User PII** (email, name) — **High**
3. **Copy audit logs** (trade history) — **High**
4. **Stripe billing data** (handled by Stripe; we store IDs only) — **Medium**
5. **Session tokens** — **High**

### 2.2 Threat Actors
| Actor | Motivation | Capability |
|-------|------------|------------|
| External attacker | Credential theft, account takeover | Network, web exploits |
| Malicious user | Access other users' accounts | Valid login, API probing |
| Insider (admin) | Data exfiltration | DB access, admin panel |
| Supply chain | Dependency compromise | npm package trojan |

### 2.3 STRIDE Analysis (Key Flows)

| Flow | Threat | Mitigation |
|------|--------|------------|
| Credential storage | Spoofing, Tampering | KMS envelope encryption; decrypt only in engine |
| API access | Elevation of privilege | Session auth; user_id scoping on all queries |
| Copy engine | Repudiation | Append-only audit log |
| Dashboard | Information disclosure | RBAC; no cross-user data leaks |
| Stripe webhook | Spoofing | Signature verification |
| Admin panel | Elevation | Separate admin role; audit admin actions |

---

## 3. Authentication & Authorization

### 3.1 User Authentication
- **Password policy:** Min 12 characters; bcrypt cost factor 12 via Lucia
- **Session:** HTTP-only, Secure, SameSite=Lax cookie; 7-day expiry; rolling refresh
- **No JWT in localStorage** — XSS cannot steal long-lived tokens
- **Email verification** required before broker connect
- **Password reset:** Single-use token, 1-hour expiry, invalidated on use

### 3.2 Rate Limiting
| Endpoint | Limit |
|----------|-------|
| `POST /auth/login` | 5 req/min/IP; lockout 15 min after 10 failures |
| `POST /auth/register` | 3 req/min/IP |
| `POST /auth/forgot-password` | 3 req/hour/email |
| API general | 100 req/min/user |
| Stripe webhook | 1000 req/min (Stripe IP ranges) |

Implementation: `@fastify/rate-limit` with Redis backend.

### 3.3 Authorization (RBAC)

| Role | Permissions |
|------|-------------|
| `trader` | Own users, accounts, copy groups, events |
| `admin` | Read all users; read aggregate stats; no decrypt credentials |

**Row-level security pattern:** Every DB query includes `WHERE user_id = :sessionUserId`. Enforced in repository layer, not ad hoc in routes.

```typescript
// DO: repository enforces ownership
async getCopyGroup(userId: UserId, groupId: string) {
  return db.query.copyGroups.findFirst({
    where: and(eq(copyGroups.id, groupId), eq(copyGroups.userId, userId)),
  });
}
```

### 3.4 CSRF Protection
- SameSite=Lax cookies provide baseline protection
- State-changing API calls from web include `X-CSRF-Token` header (double-submit cookie pattern)
- Stripe webhooks exempt (signature verified instead)

---

## 4. Credential Protection

### 4.1 Envelope Encryption Architecture

```
┌─────────────┐     ┌──────────────┐     ┌─────────────┐
│  Plaintext  │────►│  AES-256-GCM │────►│  Encrypted  │
│  credential │     │  (unique DEK)│     │  blob + IV  │
└─────────────┘     └──────┬───────┘     └──────┬──────┘
                           │                    │
                    ┌──────▼───────┐            │
                    │  AWS KMS     │            │
                    │  Wrap DEK    │            │
                    └──────────────┘            │
                                                ▼
                                         PostgreSQL
                                         credentials_encrypted
```

**Steps:**
1. Generate random 256-bit DEK per credential
2. Encrypt credential with AES-256-GCM (DEK + random IV)
3. Wrap DEK with AWS KMS CMK (`Encrypt` API)
4. Store `{ ciphertext, iv, wrappedDek, kmsKeyId }` in PostgreSQL
5. Decrypt only in `apps/engine` and `apps/workers` — never in `apps/api` response paths or `apps/web`

### 4.2 Key Management
| Key | Storage | Rotation |
|-----|---------|----------|
| KMS CMK | AWS KMS | Annual auto-rotation |
| DEK | Wrapped in DB blob | Per credential (new DEK on reconnect) |
| Session secret | AWS Secrets Manager | 90 days |
| Stripe keys | Secrets Manager | On compromise |

### 4.3 Credential Lifecycle
```
Connect → Encrypt → Store → Engine decrypts in memory → Use for WS
Disconnect → Delete blob → Schedule purge confirmation
Account deletion → Purge within 30 days (GDPR)
```

**Memory:** Credentials zeroed from memory on disconnect (overwrite buffer); engine process memory not swap-enabled (ECS config).

---

## 5. Network Security

### 5.1 Production Architecture
```
Internet → CloudFront (TLS 1.2+) → WAF → ALB → ECS (private subnets)
                                              ↓
                                    RDS + Redis (private subnets, no public IP)
                                              ↓
                                    NAT Gateway → Tradovate API (HTTPS/WSS)
```

### 5.2 Security Groups
| Service | Inbound | Outbound |
|---------|---------|----------|
| ALB | 443 from CloudFront | ECS tasks only |
| ECS (api/web) | ALB only | RDS, Redis, NAT |
| ECS (engine) | None (no ALB) | RDS, Redis, Tradovate, NAT |
| RDS | ECS security group :5432 | None |
| Redis | ECS security group :6379 | None |

### 5.3 TLS
- All external traffic TLS 1.2+ (CloudFront + ALB)
- RDS and Redis connections use TLS in production
- Tradovate WSS: certificate validation enforced

### 5.4 WAF Rules (CloudFront)
- AWS Managed Rules: Common Rule Set, Known Bad Inputs
- Rate limit: 2000 req/5min/IP on `/auth/*`
- Geo block: none initially (US/CA/global traders)

---

## 6. Application Security

### 6.1 Input Validation
- Zod schemas on all API inputs
- Reject unknown fields (`strict()` mode)
- Max request body size: 1MB
- Symbol names validated against allowlist pattern `^[A-Z0-9.]+$`

### 6.2 Output Encoding
- React auto-escapes XSS in dashboard
- API returns JSON only (no HTML)
- Content-Security-Policy header on web:

```
default-src 'self';
script-src 'self';
style-src 'self' 'unsafe-inline';
connect-src 'self' https://api.relay.trade;
frame-ancestors 'none';
```

### 6.3 SQL Injection
- Drizzle ORM parameterized queries exclusively
- No dynamic SQL string concatenation

### 6.4 Dependency Security
- Dependabot enabled on GitHub
- `pnpm audit` in CI; fail on critical/high
- Lockfile committed; no floating version ranges in production deps

### 6.5 Secrets in Code
- gitleaks scan in CI
- Pre-commit hook blocks `.env` files
- No secrets in Docker images; injected at runtime from Secrets Manager

---

## 7. Copy Engine Security

### 7.1 Integrity Controls
- **Idempotency:** Dedupe key prevents double-copy on WS reconnect replay
- **Append-only audit:** `copy_events` table — INSERT-only DB role
- **Order mapping integrity:** Unique constraint prevents duplicate follower orders for same leader leg

### 7.2 Risk Engine as Safety Gate
- Pre-copy risk check cannot be bypassed via API (engine enforces, not client)
- Live mode requires `sim_validated = true` AND active subscription (API + engine double-check)
- Locked followers reject copies at engine level regardless of API state

### 7.3 Tradovate API Security
- Store minimum credential scope needed
- Token refresh without storing refresh token in logs
- On auth failure: mark account `error`, alert user, don't retry with same creds indefinitely (lockout prevention)

---

## 8. Logging & Monitoring Security

### 8.1 What Gets Logged
| Field | Logged |
|-------|--------|
| user_id, account_id, order_id | ✅ |
| correlationId, latencyMs, action | ✅ |
| Passwords, tokens, credentials | ❌ Never |
| Encrypted credential blobs | ❌ Never |
| Full Tradovate WS payload | Staging only, debug level |

### 8.2 Security Monitoring & Alerts
| Event | Alert |
|-------|-------|
| 10+ failed logins same IP | PagerDuty / email |
| Admin action | Audit log + Slack |
| KMS decrypt failure spike | PagerDuty |
| Copy failure rate > 5% (5 min window) | On-call |
| Unusual outbound traffic from engine | AWS GuardDuty |

### 8.3 Audit Trail
- Admin actions logged to `admin_audit_log` table (Phase 2 formal; MVP: structured logs)
- Credential decrypt events logged with `accountId`, `service`, `timestamp` (not credential content)

---

## 9. Infrastructure Security

### 9.1 IAM (Least Privilege)
| Service | Permissions |
|---------|-------------|
| ECS task (api) | Secrets Manager read (session, stripe); KMS decrypt (none — api doesn't decrypt creds) |
| ECS task (engine) | Secrets Manager read; KMS decrypt (credential CMK); RDS, Redis |
| ECS task (workers) | Same as engine |
| CI/CD role | ECR push; ECS deploy; no production DB access |

### 9.2 Container Security
- Non-root user in Dockerfiles (`USER node`)
- Read-only root filesystem where possible
- No SSH into containers; ECS Exec disabled in prod
- Image scanning in ECR on push

### 9.3 Backup & Recovery
- RDS automated backups: 7-day retention
- Point-in-time recovery enabled
- Redis: persistence AOF for queue durability (BullMQ job recovery)
- RTO: 4 hours; RPO: 1 hour

---

## 10. Privacy & Compliance

### 10.1 GDPR / CCPA (MVP Baseline)
| Requirement | Implementation |
|-------------|----------------|
| Privacy policy | Published before launch |
| Data minimization | Collect email + broker creds only |
| Right to deletion | Account delete → 30-day purge job |
| Data export | Phase 2: JSON export endpoint |
| Cookie consent | Essential cookies only (session); banner if analytics added |

### 10.2 Data Classification
| Class | Examples | Handling |
|-------|----------|----------|
| Critical | Broker credentials | KMS encrypted; decrypt engine only |
| Confidential | Email, trade audit | Encrypted at rest (RDS); access controlled |
| Internal | Aggregated metrics | Standard protection |
| Public | Marketing content | CDN |

### 10.3 SOC 2 Roadmap
| Phase | Milestone |
|-------|-----------|
| MVP launch | Security plan documented; controls implemented |
| Month 6 | Gap assessment; policy docs (access, incident response) |
| Month 12 | SOC 2 Type I audit |

---

## 11. Incident Response

### 11.1 Severity Levels
| Level | Example | Response Time |
|-------|---------|---------------|
| P0 | Credential breach; mass copy failure | 15 min |
| P1 | Single user account compromise | 1 hour |
| P2 | Elevated error rate; WS outage | 4 hours |
| P3 | Non-critical vulnerability | Next sprint |

### 11.2 Credential Breach Playbook
1. **Detect** — GuardDuty alert, user report, or audit anomaly
2. **Contain** — Revoke affected KMS key access; force disconnect all broker accounts
3. **Assess** — Determine scope (which users, time window)
4. **Notify** — Email affected users within 72 hours (GDPR)
5. **Remediate** — Rotate KMS CMK; require credential re-entry
6. **Post-mortem** — Document root cause within 5 business days

### 11.3 Copy Failure Incident
1. Engine auto-pauses affected followers after 3 failures
2. On-call investigates via Grafana + audit log
3. If platform-wide: activate status page; consider master kill switch
4. Root cause fix + replay NOT automatic (manual user confirmation)

---

## 12. Security Testing Plan

| Test | When | Tool/Method |
|------|------|-------------|
| SAST | Every PR | ESLint security plugins |
| Dependency scan | Every PR | pnpm audit, Dependabot |
| Secret scan | Every PR | gitleaks |
| OWASP Top 10 self-assessment | Sprint 9 | Manual checklist |
| Penetration test | Pre-launch | External vendor (budget $5–10k) |
| Tradovate conformance | Sprint 1, 8 | Official Stage 2 websocket tests |

### MVP Security Checklist (Launch Blocker)
- [ ] Credentials encrypted with KMS envelope encryption
- [ ] No credentials in logs (automated scan green)
- [ ] Session cookies: HttpOnly, Secure, SameSite
- [ ] Rate limiting on auth endpoints
- [ ] WAF enabled on CloudFront
- [ ] RDS not publicly accessible
- [ ] All ECS tasks in private subnets
- [ ] Stripe webhook signature verification
- [ ] CSRF protection on mutations
- [ ] TLS 1.2+ enforced
- [ ] Dependabot alerts resolved (no critical/high open)
- [ ] Privacy policy + ToS published
- [ ] Incident response contact documented

---

## 13. Third-Party Security

| Vendor | Data Shared | Controls |
|--------|-------------|----------|
| Tradovate | Broker credentials, orders | TLS; encrypted storage; minimal scope |
| Stripe | Email, payment method (Stripe-hosted) | PCI SAQ-A; webhook signatures |
| Resend | Email addresses | TLS; transactional only |
| AWS | All infrastructure | Shared responsibility model; IAM least privilege |
| Grafana Cloud | Logs/metrics (no credentials) | Scrub PII from logs; no credential fields |
| Sentry | Error context (scrubbed) | `beforeSend` scrubber for tokens |

---

## 14. Secure Development Lifecycle

```
Design → Threat model review (this doc)
   ↓
Code → Coding standards + PR review + CI scans
   ↓
Test → Security test cases in copy/risk suites
   ↓
Deploy → Terraform reviewed; secrets via Secrets Manager
   ↓
Operate → Monitoring + incident response
```

Security review required for PRs touching:
- `credential-service.ts`
- `apps/engine/` hot path
- `infra/terraform/`
- Auth/session code

---

## Related Documents
- [CODING_STANDARDS.md](./CODING_STANDARDS.md)
- [HIGH_LEVEL_ARCHITECTURE.md](./HIGH_LEVEL_ARCHITECTURE.md)
- [TECHNOLOGY_DECISIONS.md](./TECHNOLOGY_DECISIONS.md)
- [SRS.md](./SRS.md) §5.3
