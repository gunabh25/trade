# Folder Structure
## Relay Monorepo Layout

**Version:** 1.0  
**Date:** June 26, 2026  
**Phase:** 0B

---

## 1. Repository Root

```
relay/
├── .github/
│   ├── workflows/
│   │   ├── ci.yml                 # Lint, test, typecheck on PR
│   │   ├── deploy-staging.yml     # Deploy to staging on main
│   │   └── deploy-prod.yml        # Deploy to prod on tag v*
│   └── PULL_REQUEST_TEMPLATE.md
│
├── apps/
│   ├── web/                       # Next.js dashboard
│   ├── api/                       # Fastify REST API
│   ├── engine/                    # Copy engine (long-running)
│   └── workers/                   # BullMQ job consumers
│
├── packages/
│   ├── broker-tradovate/          # Tradovate REST + WS adapter
│   ├── copy-core/                 # Copy orchestration, sizing, brackets
│   ├── risk/                      # Risk evaluator, P&L monitor
│   ├── db/                        # Drizzle schema, migrations, repos
│   ├── shared/                    # Types, constants, BrokerAdapter iface
│   ├── email/                     # React Email templates
│   └── config-eslint/             # Shared ESLint config
│   └── config-typescript/         # Shared tsconfig bases
│
├── infra/
│   ├── terraform/
│   │   ├── modules/
│   │   │   ├── ecs/
│   │   │   ├── rds/
│   │   │   ├── redis/
│   │   │   └── networking/
│   │   ├── environments/
│   │   │   ├── staging/
│   │   │   └── prod/
│   │   └── backend.tf
│   └── docker/
│       ├── Dockerfile.web
│       ├── Dockerfile.api
│       ├── Dockerfile.engine
│       └── Dockerfile.workers
│
├── docs/
│   ├── phase-0a/                  # Product research
│   └── phase-0b/                  # Architecture (this phase)
│
├── scripts/
│   ├── dev.sh                     # Start full local stack
│   ├── db-migrate.sh              # Run Drizzle migrations
│   ├── db-seed.sh                 # Seed dev data
│   └── tradovate-smoke.ts         # Tradovate API connectivity test
│
├── .env.example                   # Root env template (no secrets)
├── docker-compose.yml             # Local: postgres, redis, mailpit
├── package.json                   # Root workspace config
├── pnpm-workspace.yaml
├── turbo.json
├── tsconfig.json                  # Root TS references
└── README.md
```

---

## 2. App: `apps/web`

```
apps/web/
├── src/
│   ├── app/                       # Next.js App Router
│   │   ├── (auth)/
│   │   │   ├── login/page.tsx
│   │   │   ├── register/page.tsx
│   │   │   └── reset-password/page.tsx
│   │   ├── (dashboard)/
│   │   │   ├── layout.tsx
│   │   │   ├── page.tsx           # Overview
│   │   │   ├── accounts/
│   │   │   ├── copy-group/
│   │   │   ├── events/
│   │   │   ├── notifications/
│   │   │   └── settings/
│   │   │       └── billing/
│   │   ├── (admin)/
│   │   │   └── admin/
│   │   ├── api/                   # Optional BFF routes (minimal)
│   │   ├── layout.tsx
│   │   └── globals.css
│   ├── components/
│   │   ├── ui/                    # shadcn/ui primitives
│   │   ├── copy-group/
│   │   ├── events/
│   │   ├── accounts/
│   │   └── layout/
│   ├── hooks/
│   │   ├── use-copy-events-sse.ts
│   │   └── use-copy-group.ts
│   ├── lib/
│   │   ├── api-client.ts          # Typed fetch wrapper to apps/api
│   │   └── utils.ts
│   └── types/
│       └── index.ts               # Re-export from @relay/shared
├── public/
├── next.config.ts
├── tailwind.config.ts
├── package.json
└── tsconfig.json
```

---

## 3. App: `apps/api`

```
apps/api/
├── src/
│   ├── index.ts                   # Fastify bootstrap
│   ├── plugins/
│   │   ├── auth.ts                # Session validation
│   │   ├── cors.ts
│   │   └── error-handler.ts
│   ├── routes/
│   │   ├── auth/
│   │   ├── broker-accounts/
│   │   ├── copy-groups/
│   │   ├── copy-events/
│   │   ├── notifications/
│   │   ├── billing/
│   │   ├── webhooks/
│   │   │   └── stripe.ts
│   │   ├── admin/
│   │   └── health.ts
│   ├── services/
│   │   ├── auth-service.ts
│   │   ├── broker-account-service.ts
│   │   ├── copy-group-service.ts
│   │   ├── billing-service.ts
│   │   ├── credential-service.ts  # Encrypt/decrypt via KMS
│   │   └── engine-command-service.ts  # Redis publish
│   ├── middleware/
│   │   ├── require-auth.ts
│   │   ├── require-admin.ts
│   │   └── require-subscription.ts
│   └── sse/
│       └── copy-events-stream.ts
├── package.json
└── tsconfig.json
```

---

## 4. App: `apps/engine`

```
apps/engine/
├── src/
│   ├── index.ts                   # Process entry; graceful shutdown
│   ├── registry/
│   │   ├── group-registry.ts      # Active copy groups in memory
│   │   └── connection-pool.ts     # Account → TradovateConnection map
│   ├── pipeline/
│   │   ├── leader-event-handler.ts
│   │   ├── copy-orchestrator.ts
│   │   ├── size-calculator.ts
│   │   └── audit-writer.ts        # Async batch insert
│   ├── listeners/
│   │   ├── command-listener.ts    # Redis engine:commands
│   │   └── config-cache.ts
│   ├── monitors/
│   │   └── pnl-monitor.ts
│   └── shutdown.ts                # SIGTERM: flush audit, close WS
├── package.json
└── tsconfig.json
```

---

## 5. App: `apps/workers`

```
apps/workers/
├── src/
│   ├── index.ts                   # BullMQ worker registry
│   ├── queues/
│   │   ├── reconciliation.worker.ts
│   │   ├── token-refresh.worker.ts
│   │   ├── alerts.worker.ts
│   │   └── daily-reset.worker.ts
│   └── schedulers/
│       └── cron.ts                # Repeatable job registration
├── package.json
└── tsconfig.json
```

---

## 6. Package: `packages/broker-tradovate`

```
packages/broker-tradovate/
├── src/
│   ├── adapter.ts                 # Implements BrokerAdapter
│   ├── client/
│   │   ├── rest-client.ts
│   │   ├── ws-client.ts
│   │   └── token-manager.ts
│   ├── mappers/
│   │   ├── order-mapper.ts
│   │   └── event-mapper.ts
│   ├── types/
│   │   └── tradovate.ts
│   └── index.ts
├── tests/
│   ├── ws-client.test.ts
│   ├── event-mapper.test.ts
│   └── adapter.integration.test.ts
├── package.json
└── tsconfig.json
```

---

## 7. Package: `packages/copy-core`

```
packages/copy-core/
├── src/
│   ├── orchestrator.ts            # Core copy planning logic
│   ├── bracket-mapper.ts          # Bracket leg tracking
│   ├── dedupe.ts
│   ├── order-mapping-store.ts     # Redis-backed mapping
│   └── index.ts
├── tests/
│   ├── orchestrator.test.ts
│   ├── bracket-mapper.test.ts
│   └── sizing.test.ts
├── package.json
└── tsconfig.json
```

---

## 8. Package: `packages/risk`

```
packages/risk/
├── src/
│   ├── evaluator.ts               # Pre-copy checks
│   ├── breach-handler.ts          # Flatten + lock logic
│   ├── pnl-calculator.ts
│   ├── follower-state.ts
│   └── index.ts
├── tests/
│   ├── evaluator.test.ts
│   ├── breach-handler.test.ts
│   └── daily-reset.test.ts
├── package.json
└── tsconfig.json
```

---

## 9. Package: `packages/db`

```
packages/db/
├── src/
│   ├── schema/
│   │   ├── users.ts
│   │   ├── subscriptions.ts
│   │   ├── broker-accounts.ts
│   │   ├── copy-groups.ts
│   │   ├── copy-events.ts
│   │   ├── notifications.ts
│   │   └── index.ts               # Combined schema export
│   ├── repos/
│   │   ├── user-repo.ts
│   │   ├── copy-group-repo.ts
│   │   ├── copy-event-repo.ts
│   │   └── broker-account-repo.ts
│   ├── client.ts                  # Drizzle client factory
│   └── index.ts
├── migrations/                    # Drizzle Kit generated SQL
├── drizzle.config.ts
├── package.json
└── tsconfig.json
```

---

## 10. Package: `packages/shared`

```
packages/shared/
├── src/
│   ├── types/
│   │   ├── domain.ts              # LeaderEvent, CopyResult, etc.
│   │   ├── api.ts                 # Request/response DTOs
│   │   └── broker-adapter.ts      # BrokerAdapter interface
│   ├── constants/
│   │   ├── limits.ts              # MVP plan limits
│   │   └── tradovate.ts           # URLs, heartbeat interval
│   ├── errors/
│   │   └── app-error.ts           # Typed error codes
│   └── index.ts
├── package.json
└── tsconfig.json
```

---

## 11. Package: `packages/email`

```
packages/email/
├── src/
│   ├── templates/
│   │   ├── verify-email.tsx
│   │   ├── reset-password.tsx
│   │   ├── copy-failure-alert.tsx
│   │   ├── breach-alert.tsx
│   │   └── connection-lost.tsx
│   ├── send.ts                    # Resend wrapper
│   └── index.ts
├── package.json
└── tsconfig.json
```

---

## 12. Workspace Configuration

### `pnpm-workspace.yaml`
```yaml
packages:
  - "apps/*"
  - "packages/*"
```

### `turbo.json` (key pipelines)
```json
{
  "$schema": "https://turbo.build/schema.json",
  "tasks": {
    "build": { "dependsOn": ["^build"], "outputs": ["dist/**", ".next/**"] },
    "dev": { "cache": false, "persistent": true },
    "lint": { "dependsOn": ["^build"] },
    "typecheck": { "dependsOn": ["^build"] },
    "test": { "dependsOn": ["^build"] },
    "test:integration": { "dependsOn": ["build"], "cache": false }
  }
}
```

---

## 13. Package Dependency Graph

```
                    ┌─────────┐
                    │   web   │
                    └────┬────┘
                         │ @relay/shared
                    ┌────▼────┐
                    │   api   │──────────────────┐
                    └────┬────┘                  │
           ┌─────────────┼─────────────┐        │
           │             │             │        │
      ┌────▼────┐   ┌────▼────┐  ┌─────▼────┐   │
      │   db    │   │  email  │  │  shared  │◄──┘
      └────┬────┘   └─────────┘  └─────▲────┘
           │                           │
      ┌────▼───────────────────────────┴────┐
      │              engine                  │
      └────┬──────────────┬──────────────────┘
           │              │
    ┌──────▼──────┐ ┌─────▼──────┐ ┌─────────┐
    │ broker-     │ │ copy-core  │ │  risk   │
    │ tradovate   │ └────────────┘ └─────────┘
    └─────────────┘
           ▲
      ┌────┴────┐
      │ workers │
      └─────────┘
```

**Rule:** Packages must not import from apps. Apps import packages. No circular deps between packages.

---

## 14. Environment Files

| File | Location | Committed |
|------|----------|-----------|
| `.env.example` | Root | Yes — template only |
| `.env.local` | Per app | No — gitignored |
| `terraform.tfvars` | `infra/terraform/environments/*/` | No |

### Required Variables (by app)

**Shared:**
```
NODE_ENV=development|staging|production
DATABASE_URL=postgresql://...
REDIS_URL=redis://...
```

**API + Engine:**
```
KMS_KEY_ID=arn:aws:kms:...
TRADOVATE_ENV=demo|live
TRADOVATE_API_KEY=...          # dev only; prod in Secrets Manager
```

**API only:**
```
STRIPE_SECRET_KEY=...
STRIPE_WEBHOOK_SECRET=...
RESEND_API_KEY=...
SESSION_SECRET=...
```

**Web only:**
```
NEXT_PUBLIC_API_URL=http://localhost:3001/v1
```

---

## 15. Naming Conventions

| Item | Convention | Example |
|------|------------|---------|
| Package names | `@relay/<name>` | `@relay/copy-core` |
| DB tables | snake_case plural | `copy_events` |
| TS files | kebab-case | `copy-orchestrator.ts` |
| React components | PascalCase file + export | `CopyGroupForm.tsx` |
| API routes | kebab-case paths | `/copy-groups/sim-test` |
| Env vars | SCREAMING_SNAKE | `DATABASE_URL` |
| Redis keys | colon-separated | `follower_state:{id}` |

---

## Related Documents
- [TECHNOLOGY_DECISIONS.md](./TECHNOLOGY_DECISIONS.md)
- [DEVELOPMENT_ROADMAP.md](./DEVELOPMENT_ROADMAP.md)
- [CODING_STANDARDS.md](./CODING_STANDARDS.md)
