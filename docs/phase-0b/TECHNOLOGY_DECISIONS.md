# Technology Decisions
## Relay — Architecture Decision Records (ADR Summary)

**Version:** 1.0  
**Date:** June 26, 2026  
**Phase:** 0B

Each decision follows: **Context → Decision → Consequences → Alternatives Considered**

---

## ADR-001: Monorepo with Turborepo

| | |
|---|---|
| **Status** | Accepted |
| **Context** | Multiple deployables (web, api, engine, workers) share domain types, DB schema, and broker adapters |
| **Decision** | pnpm workspaces + Turborepo for build orchestration |
| **Consequences** | Shared packages with type safety; single CI pipeline; slightly higher initial setup |
| **Alternatives** | Polyrepo (rejected: type drift risk); Nx (rejected: heavier for team size) |

---

## ADR-002: TypeScript Everywhere

| | |
|---|---|
| **Status** | Accepted |
| **Context** | Tradovate provides [JavaScript examples](https://api.tradovate.com/); team needs fast full-stack iteration |
| **Decision** | TypeScript 5.x for all apps and packages |
| **Consequences** | End-to-end type safety; shared interfaces between engine and API; Node.js async I/O fits WebSocket workloads |
| **Alternatives** | Go for engine (rejected MVP: split language overhead, slower iteration); Rust (rejected: overkill for MVP) |

---

## ADR-003: Three Deployables (Not Microservices)

| | |
|---|---|
| **Status** | Accepted |
| **Context** | MVP team = 2 engineers; need reliability isolation for copy engine without ops burden |
| **Decision** | 3 ECS services: `web`, `api`, `engine` + `workers` (can share task definition with api initially) |
| **Consequences** | Engine restarts don't take down dashboard; clear ownership boundaries; not full microservice complexity |
| **Alternatives** | Single monolith (rejected: WS connections lost on deploy); full microservices (rejected: premature) |

---

## ADR-004: PostgreSQL as System of Record

| | |
|---|---|
| **Status** | Accepted |
| **Context** | Relational data (users, accounts, audit log); ACID for billing state; append-only audit |
| **Decision** | PostgreSQL 16 on AWS RDS |
| **Consequences** | Strong consistency; JSONB for metadata; mature tooling; read replica path clear |
| **Alternatives** | MongoDB (rejected: relational model fits better); CockroachDB (rejected: unnecessary for MVP scale) |

---

## ADR-005: Drizzle ORM

| | |
|---|---|
| **Status** | Accepted |
| **Context** | Type-safe queries; SQL-like; lightweight migrations |
| **Decision** | Drizzle ORM + Drizzle Kit for migrations |
| **Consequences** | Excellent TS inference; no code generation step; schema in code |
| **Alternatives** | Prisma (rejected: heavier runtime); raw SQL (rejected: no type safety) |

---

## ADR-006: Redis for Queue + Pub/Sub + Cache

| | |
|---|---|
| **Status** | Accepted |
| **Context** | Need job queues, SSE fan-out, idempotency keys, in-memory state backup |
| **Decision** | Redis 7 on AWS ElastiCache; BullMQ for job processing |
| **Consequences** | Single infra component for multiple patterns; BullMQ battle-tested; TLS in prod |
| **Alternatives** | SQS + SNS (rejected: higher latency for SSE fan-out); RabbitMQ (rejected: more ops) |

---

## ADR-007: Fastify for API Service

| | |
|---|---|
| **Status** | Accepted |
| **Context** | API needs performance, schema validation, plugin ecosystem |
| **Decision** | Fastify 5 with `@fastify/cookie`, `@fastify/cors`, Zod validation |
| **Consequences** | ~2× throughput vs Express; JSON schema validation; separate from Next.js server |
| **Alternatives** | Express (rejected: slower); tRPC only (rejected: need Stripe webhooks as REST); NestJS (rejected: heavy) |

---

## ADR-008: Next.js 15 for Web App

| | |
|---|---|
| **Status** | Accepted |
| **Context** | Dashboard needs SSR, auth cookies, good DX, React ecosystem |
| **Decision** | Next.js 15 App Router; Tailwind CSS + shadcn/ui |
| **Consequences** | Fast UI development; Server Components for static pages; API calls to Fastify backend |
| **Alternatives** | Vite SPA (rejected: worse SEO/SSR); Remix (viable alternative, Next chosen for ecosystem) |

---

## ADR-009: Session Auth (Not JWT in localStorage)

| | |
|---|---|
| **Status** | Accepted |
| **Context** | Security requirement: no tokens in localStorage; XSS mitigation |
| **Decision** | Lucia Auth v3 with HTTP-only, Secure, SameSite=Lax session cookies; sessions in PostgreSQL |
| **Consequences** | CSRF protection needed on mutations; server-side session revocation; no token refresh UX |
| **Alternatives** | Auth.js (viable); JWT in memory (rejected: complexity); Clerk (rejected: cost + broker data sensitivity) |

---

## ADR-010: Credential Encryption — Envelope Encryption

| | |
|---|---|
| **Status** | Accepted |
| **Context** | Broker API keys must be encrypted at rest; engine needs decrypt at runtime |
| **Decision** | AES-256-GCM per credential with unique DEK; DEK wrapped by AWS KMS CMK |
| **Consequences** | KMS audit trail; key rotation supported; decrypt only in engine/worker processes |
| **Alternatives** | App-level master key in env (rejected: no rotation); HashiCorp Vault (Phase 2 option) |

---

## ADR-011: Tradovate WebSocket for Orders (Not REST)

| | |
|---|---|
| **Status** | Accepted |
| **Context** | Latency target P95 < 80ms; Tradovate WS supports same order endpoints as REST |
| **Decision** | WebSocket for both leader event subscription AND follower order submission |
| **Consequences** | One connection per account; heartbeat management required; lower latency |
| **Alternatives** | REST for orders (fallback only on WS failure); hybrid WS leader + REST followers (rejected: slower) |

---

## ADR-012: SSE for Dashboard Real-Time (Not WebSocket)

| | |
|---|---|
| **Status** | Accepted |
| **Context** | Dashboard needs one-way event stream; simpler than bidirectional WS through CDN |
| **Decision** | Server-Sent Events from API; API subscribes to Redis pub/sub |
| **Consequences** | Auto-reconnect built into EventSource; works through CloudFront; sufficient for MVP |
| **Alternatives** | WebSocket to browser (Phase 2 if bidirectional needed); polling (rejected: latency) |

---

## ADR-013: Stripe for Billing

| | |
|---|---|
| **Status** | Accepted |
| **Context** | SaaS subscription; trial support; customer portal |
| **Decision** | Stripe Checkout + Customer Portal + webhooks |
| **Consequences** | PCI scope minimized; proven; 7-day trial via `trial_period_days` |
| **Alternatives** | Paddle (viable for tax); LemonSqueezy (rejected: less flexible) |

---

## ADR-014: Resend for Email

| | |
|---|---|
| **Status** | Accepted |
| **Context** | Transactional email: verify, reset, alerts |
| **Decision** | Resend with React Email templates |
| **Consequences** | Simple API; good deliverability; React components for templates |
| **Alternatives** | AWS SES (viable at scale); SendGrid (rejected: heavier) |

---

## ADR-015: AWS us-east-1 Infrastructure

| | |
|---|---|
| **Status** | Accepted |
| **Context** | CME proximity; Tradovate infrastructure US-based; mature ECS/RDS |
| **Decision** | AWS us-east-1: ECS Fargate, RDS PostgreSQL, ElastiCache Redis, Secrets Manager, CloudFront, WAF |
| **Consequences** | Single region MVP; ~$200–400/mo infra at beta scale |
| **Alternatives** | GCP Cloud Run (viable); Railway/Fly.io for MVP (rejected: need KMS, WAF for prod path); Hetzner (rejected: latency) |

---

## ADR-016: Observability Stack

| | |
|---|---|
| **Status** | Accepted |
| **Context** | Debug copy failures; latency SLO monitoring; alert on engine health |
| **Decision** | OpenTelemetry SDK → Grafana Cloud (logs, metrics, traces); Sentry for error tracking |
| **Consequences** | Correlation IDs across engine/API; copy latency histograms; free tier sufficient for MVP |
| **Alternatives** | Datadog (cost at scale); CloudWatch only (rejected: poor trace UX) |

---

## ADR-017: Testing Strategy

| | |
|---|---|
| **Status** | Accepted |
| **Context** | Copy logic and risk rules are safety-critical |
| **Decision** | Vitest for unit tests; Tradovate demo API for integration tests; k6 for load; Playwright for E2E |
| **Consequences** | 80% coverage target on `copy-core`, `risk`, `broker-tradovate` |
| **Alternatives** | Jest (rejected: Vitest faster in monorepo) |

---

## ADR-018: CI/CD — GitHub Actions

| | |
|---|---|
| **Status** | Accepted |
| **Context** | Monorepo needs lint, test, build, deploy pipeline |
| **Decision** | GitHub Actions: PR → lint + test + typecheck; main → deploy staging; tag → deploy prod |
| **Consequences** | Turborepo remote cache optional; ECS deploy via AWS CLI |
| **Alternatives** | CircleCI (viable); manual deploy (rejected) |

---

## ADR-019: Broker Adapter Interface (Pluggable)

| | |
|---|---|
| **Status** | Accepted |
| **Context** | Phase 2 adds Rithmic, TradingView; avoid engine rewrite |
| **Decision** | `BrokerAdapter` interface in `packages/shared`; Tradovate implements first |

```typescript
interface BrokerAdapter {
  connect(account: BrokerAccount): Promise<ConnectionHandle>;
  disconnect(handle: ConnectionHandle): Promise<void>;
  subscribeLeaderEvents(handle: ConnectionHandle, cb: EventCallback): void;
  placeOrder(handle: ConnectionHandle, order: DomainOrder): Promise<OrderResult>;
  modifyOrder(handle: ConnectionHandle, mod: DomainModify): Promise<OrderResult>;
  cancelOrder(handle: ConnectionHandle, orderId: number): Promise<void>;
  getPositions(handle: ConnectionHandle): Promise<Position[]>;
  flattenAll(handle: ConnectionHandle): Promise<void>;
}
```

| **Consequences** | Engine is broker-agnostic; new adapters are additive packages |
| **Alternatives** | Tradovate hardcoded in engine (rejected: Phase 2 pain) |

---

## ADR-020: Infrastructure as Code — Terraform

| | |
|---|---|
| **Status** | Accepted |
| **Context** | Reproducible staging/prod; team needs reviewable infra changes |
| **Decision** | Terraform for AWS resources; Docker images via GitHub Actions |
| **Consequences** | `infra/terraform/` with env workspaces (`staging`, `prod`) |
| **Alternatives** | AWS CDK (viable); Pulumi (viable); click-ops (rejected) |

---

## Technology Stack Summary

| Layer | Choice | Version |
|-------|--------|---------|
| Language | TypeScript | 5.4+ |
| Runtime | Node.js | 22 LTS |
| Monorepo | Turborepo + pnpm | latest |
| Web | Next.js + Tailwind + shadcn/ui | 15.x |
| API | Fastify + Zod | 5.x |
| Auth | Lucia | 3.x |
| ORM | Drizzle | 0.30+ |
| Database | PostgreSQL | 16 |
| Cache/Queue | Redis + BullMQ | 7.x / 5.x |
| Billing | Stripe | API 2024-11-20 |
| Email | Resend + React Email | latest |
| Testing | Vitest + Playwright + k6 | latest |
| IaC | Terraform | 1.8+ |
| Cloud | AWS us-east-1 | ECS Fargate |
| Observability | OpenTelemetry + Grafana Cloud + Sentry | latest |

---

## Related Documents
- [HIGH_LEVEL_ARCHITECTURE.md](./HIGH_LEVEL_ARCHITECTURE.md)
- [LOW_LEVEL_DESIGN.md](./LOW_LEVEL_DESIGN.md)
- [FOLDER_STRUCTURE.md](./FOLDER_STRUCTURE.md)
