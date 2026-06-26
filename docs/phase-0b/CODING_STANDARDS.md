# Coding Standards
## Relay — Engineering Conventions

**Version:** 1.0  
**Date:** June 26, 2026  
**Phase:** 0B

---

## 1. General Principles

1. **Correctness over cleverness** — Copy engine and risk code must be boring and testable
2. **Explicit over implicit** — No magic; config and state transitions are named and logged
3. **Fail loud** — Never swallow errors on the copy hot path; log + alert + structured error
4. **Minimal scope** — PRs do one thing; no drive-by refactors
5. **Match existing patterns** — Before adding abstractions, find the nearest similar code

---

## 2. TypeScript

### 2.1 Compiler Options (strict)
All packages extend `@relay/config-typescript/base.json`:
```json
{
  "compilerOptions": {
    "strict": true,
    "noUncheckedIndexedAccess": true,
    "exactOptionalPropertyTypes": true,
    "noImplicitReturns": true,
    "noFallthroughCasesInSwitch": true
  }
}
```

### 2.2 Types
- Prefer `interface` for object shapes; `type` for unions and mapped types
- No `any` — use `unknown` and narrow with Zod or type guards
- Domain types live in `@relay/shared`; don't duplicate DTOs across apps
- Use branded types for IDs where confusion is costly:

```typescript
type UserId = string & { readonly brand: unique symbol };
type BrokerAccountId = string & { readonly brand: unique symbol };
```

### 2.3 Nullability
- Use `| null` for intentionally absent values in DB/API
- Avoid `undefined` in public API responses; serialize null explicitly
- Optional chaining is fine; non-null assertions (`!`) require a comment explaining why

---

## 3. Naming

| Item | Convention | Example |
|------|------------|---------|
| Variables, functions | camelCase | `calculateFollowerQuantity` |
| Classes | PascalCase | `CopyOrchestrator` |
| Constants | SCREAMING_SNAKE | `HEARTBEAT_INTERVAL_MS` |
| Files | kebab-case | `copy-orchestrator.ts` |
| React components | PascalCase file | `CopyGroupForm.tsx` |
| DB columns | snake_case | `daily_loss_limit_usd` |
| API paths | kebab-case | `/copy-groups/sim-test` |
| Enums (TS) | PascalCase name, PascalCase values | `CopyMode.Sim` |

---

## 4. Project Structure Rules

### 4.1 Layer Boundaries
```
apps/*     → may import packages/*
packages/* → may import other packages (no cycles)
packages/* → must NOT import apps/*
```

### 4.2 File Organization (within a module)
```typescript
// 1. External imports
// 2. Internal package imports
// 3. Types/interfaces
// 4. Constants
// 5. Main export(s)
// 6. Private helpers
```

### 4.3 Export Rules
- Each package exposes a single `index.ts` public API
- Don't export internals from package root; use subpath imports only in tests

---

## 5. Error Handling

### 5.1 AppError (typed errors)
Use `@relay/shared/errors`:

```typescript
throw new AppError('FOLLOWER_LOCKED', 'Follower is locked after daily loss breach', {
  statusCode: 422,
  meta: { followerId },
});
```

### 5.2 Engine Hot Path
```typescript
// DO: log, record failure event, continue other followers
const results = await Promise.allSettled(followers.map(copyToFollower));
for (const result of results) {
  if (result.status === 'rejected') {
    logger.error({ err: result.reason, followerId }, 'copy_failed');
    await alertQueue.add('copy-failure', { ... });
  }
}

// DON'T: throw on single follower failure (blocks other followers)
```

### 5.3 Never Log Secrets
```typescript
// DO
logger.info({ accountId, orderId }, 'order_placed');

// DON'T
logger.info({ credentials, accessToken }, 'connected');
```

---

## 6. Logging

### 6.1 Logger
Use `pino` with structured JSON:

```typescript
const logger = pino({ name: 'engine:copy-orchestrator' });

logger.info({
  correlationId,
  copyGroupId,
  leaderOrderId,
  latencyMs,
}, 'copy_event_completed');
```

### 6.2 Correlation IDs
- API generates `correlationId` (UUID) per request; passes via header to downstream
- Engine generates `correlationId` per leader event; attaches to all follower copies and audit rows

### 6.3 Log Levels
| Level | Usage |
|-------|-------|
| `error` | Copy failures, connection failures, breach events |
| `warn` | Retries, drift detected, token refresh failures |
| `info` | Copy success, connect/disconnect, config reload |
| `debug` | WS raw messages (dev/staging only; never prod) |

---

## 7. API Conventions

### 7.1 Request Validation
All inputs validated with Zod at route boundary:

```typescript
const ConnectAccountSchema = z.object({
  username: z.string().min(1),
  password: z.string().min(1),
  environment: z.enum(['demo', 'live']),
  role: z.enum(['leader', 'follower']),
});
```

### 7.2 Response Shape
```typescript
// Success
{ "data": { ... } }

// Error
{ "error": { "code": "FOLLOWER_LOCKED", "message": "..." } }

// Paginated
{ "data": [...], "meta": { "page": 1, "pageSize": 50, "total": 123 } }
```

### 7.3 HTTP Status Codes
| Code | Usage |
|------|-------|
| 200 | Success |
| 201 | Created |
| 400 | Validation error |
| 401 | Not authenticated |
| 402 | Subscription required |
| 403 | Forbidden |
| 404 | Not found |
| 409 | Conflict (duplicate account) |
| 422 | Business rule violation |
| 429 | Rate limited |
| 500 | Internal error (never expose stack) |

---

## 8. Database

### 8.1 Migrations
- All schema changes via Drizzle Kit: `pnpm db:generate` → review SQL → `pnpm db:migrate`
- Never edit applied migrations; create new ones
- Migrations must be backward-compatible for zero-downtime deploys (add column nullable first)

### 8.2 Queries
- Use Drizzle query builder; raw SQL only with comment justification
- Repositories in `@relay/db/repos` — apps don't query tables directly
- Transactions for multi-table writes:

```typescript
await db.transaction(async (tx) => {
  await tx.update(copyGroupFollowers).set({ status: 'locked' }).where(...);
  await tx.insert(copyEvents).values({ action: 'breach', ... });
});
```

### 8.3 copy_events
- INSERT only in application code
- Never UPDATE or DELETE — enforced by DB role in production

---

## 9. Testing

### 9.1 Coverage Targets
| Package | Min Coverage |
|---------|--------------|
| `copy-core` | 90% |
| `risk` | 90% |
| `broker-tradovate` | 80% |
| `apps/api` services | 70% |
| `apps/engine` pipeline | 80% |
| `apps/web` | E2E critical paths |

### 9.2 Test Naming
```typescript
describe('SizeCalculator', () => {
  describe('ratio mode', () => {
    it('rounds leader qty multiplied by ratio', () => { ... });
    it('returns 0 when result is below 1 contract', () => { ... });
  });
});
```

### 9.3 Test Categories
| Type | Location | Run |
|------|----------|-----|
| Unit | `packages/*/tests/` | Every PR |
| Integration | `*.integration.test.ts` | PR + nightly (needs Tradovate demo) |
| E2E | `apps/web/e2e/` | Nightly + pre-release |
| Load | `scripts/load/` | Pre-beta, pre-launch |

### 9.4 Mocking
- Mock external services (Tradovate, Stripe, Resend) in unit tests
- Use Tradovate demo API for integration tests — never live credentials in CI
- Don't mock `copy-core` or `risk` in engine tests — test real pipeline

---

## 10. Git & Code Review

### 10.1 Branch Naming
```
feature/copy-bracket-orders
fix/token-refresh-race
chore/upgrade-drizzle
```

### 10.2 Commit Messages
Conventional Commits:
```
feat(engine): propagate bracket stop modifications
fix(risk): reset daily PnL at session boundary
test(copy-core): add partial fill scenarios
chore(deps): bump fastify to 5.2
```

### 10.3 PR Requirements
- Title follows conventional commit format
- Description: what, why, test plan
- ≤ 400 lines changed (split larger work)
- 1 approving review required
- CI green
- No merge if copy-core or risk coverage drops

### 10.4 Review Focus Areas
| Path | Reviewer Checks |
|------|-----------------|
| `apps/engine/` | Latency impact, error isolation, idempotency |
| `packages/risk/` | Breach correctness, per-account isolation |
| `packages/broker-tradovate/` | WS protocol compliance, heartbeat |
| `apps/api/` | Auth, input validation, no credential leaks |
| `infra/` | Security groups, least privilege IAM |

---

## 11. React / Frontend

### 11.1 Components
- Prefer Server Components for static layout; Client Components only when needed (SSE, forms)
- Co-locate component-specific hooks in same directory
- Use shadcn/ui primitives; don't reinvent buttons, dialogs, tables

### 11.2 Data Fetching
- Server Components fetch via internal API for initial load
- Client mutations via typed `api-client.ts` wrapper
- SSE for real-time event feed — no polling

### 11.3 Styling
- Tailwind CSS utility classes
- No inline styles except dynamic values
- Dark mode: support from launch (traders often prefer dark UI)

---

## 12. Engine-Specific Rules

### 12.1 Hot Path Prohibitions
On the copy hot path (`leader event → follower submit`):
- ❌ No synchronous HTTP calls
- ❌ No unbounded DB queries (use in-memory cache)
- ❌ No `await` on audit write (use async buffer)
- ❌ No global locks across followers

### 12.2 Idempotency
Every leader event processed with dedupe key before any side effect:
```typescript
const dedupeKey = `${accountId}:${tradovateEventId}`;
```

### 12.3 Graceful Shutdown
On SIGTERM:
1. Stop accepting new leader events
2. Flush audit buffer (max 5s wait)
3. Close WebSocket connections cleanly
4. Exit 0

---

## 13. Linting & Formatting

| Tool | Config |
|------|--------|
| ESLint | `@relay/config-eslint` — flat config, typescript-eslint |
| Prettier | Single quotes, trailing comma es5, printWidth 100 |
| Husky | pre-commit: lint-staged (eslint + prettier on changed files) |

```json
// .lintstagedrc.json
{
  "*.{ts,tsx}": ["eslint --fix", "prettier --write"],
  "*.{json,md}": ["prettier --write"]
}
```

---

## 14. Documentation

- Public API: inline JSDoc on exported functions in packages
- Complex logic: short comment explaining **why**, not what
- Architecture changes: update `docs/phase-0b/` in same PR
- README per app with: purpose, env vars, dev commands

---

## 15. Security Coding Rules (Summary)

See [SECURITY_PLAN.md](./SECURITY_PLAN.md) for full detail.

- Never store plaintext broker credentials
- Never log tokens, passwords, or encrypted blobs
- Validate all user input at API boundary
- Parameterized queries only (Drizzle handles this)
- CSRF token on state-changing web forms
- Rate limit auth endpoints
- Dependabot enabled; patch critical CVEs within 48h

---

## Related Documents
- [SECURITY_PLAN.md](./SECURITY_PLAN.md)
- [TECHNOLOGY_DECISIONS.md](./TECHNOLOGY_DECISIONS.md)
- [FOLDER_STRUCTURE.md](./FOLDER_STRUCTURE.md)
