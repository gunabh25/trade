# TradeFlow AI — Documentation Index

## Foundation (Phase 1)

| Document                                  | Description                                        |
| ----------------------------------------- | -------------------------------------------------- |
| [ARCHITECTURE.md](./ARCHITECTURE.md)      | Foundation architectural decisions                 |
| [Database Design](./database/DATABASE.md) | PostgreSQL schema, ER diagram, indexes, migrations |
| [Authentication API](./api/AUTH.md)       | Auth endpoints, JWT, OAuth, 2FA, security controls |
| [README](../README.md)                    | Setup, commands, full decision log                 |

## Phase 0A — Product Research (Relay / prior planning)

| Document                                                 | Description                         |
| -------------------------------------------------------- | ----------------------------------- |
| [PRD](./phase-0a/PRD.md)                                 | Product Requirements Document       |
| [Competitor Analysis](./phase-0a/COMPETITOR_ANALYSIS.md) | Market and competitor deep dive     |
| [Feature Matrix](./phase-0a/FEATURE_MATRIX.md)           | Side-by-side feature comparison     |
| [MVP Definition](./phase-0a/MVP_DEFINITION.md)           | MVP scope, timeline, future roadmap |

## Phase 0B — System Architecture

| Document                                                         | Description                                |
| ---------------------------------------------------------------- | ------------------------------------------ |
| [SRS](./phase-0b/SRS.md)                                         | Software Requirements Specification        |
| [High-Level Architecture](./phase-0b/HIGH_LEVEL_ARCHITECTURE.md) | C4 diagrams, services, data flows          |
| [Low-Level Design](./phase-0b/LOW_LEVEL_DESIGN.md)               | DB schema, APIs, state machines, sequences |
| [Technology Decisions](./phase-0b/TECHNOLOGY_DECISIONS.md)       | ADRs and stack summary                     |
| [Folder Structure](./phase-0b/FOLDER_STRUCTURE.md)               | Monorepo layout                            |
| [Development Roadmap](./phase-0b/DEVELOPMENT_ROADMAP.md)         | 12-week sprint plan                        |
| [Coding Standards](./phase-0b/CODING_STANDARDS.md)               | Engineering conventions                    |
| [Security Plan](./phase-0b/SECURITY_PLAN.md)                     | Security architecture and controls         |

## Production Readiness

| Document                                                   | Description                                 |
| ---------------------------------------------------------- | ------------------------------------------- |
| [Architecture Review](./production/ARCHITECTURE_REVIEW.md) | Production topology, middleware, deployment |
| [Security Report](./production/SECURITY_REPORT.md)         | OWASP, JWT, OAuth, rate limits, secrets     |
| [Performance Report](./production/PERFORMANCE_REPORT.md)   | DB, Redis, caching, Prometheus metrics      |
| [Optimization Report](./production/OPTIMIZATION_REPORT.md) | Summary of changes and deploy commands      |
| [.env.production.example](../.env.production.example)      | Production environment template             |

## Architecture Summary

```
┌──────────┐   ┌──────────┐   ┌──────────────┐   ┌──────────┐
│ Next.js  │   │ Fastify  │   │ Copy Engine  │   │ Workers  │
│   Web    │──►│   API    │   │ (Tradovate   │   │ (BullMQ) │
│          │   │          │   │  WebSocket)  │   │          │
└──────────┘   └────┬─────┘   └──────┬───────┘   └────┬─────┘
                    │                │                 │
                    └────────────────┼─────────────────┘
                                     ▼
                          PostgreSQL + Redis (AWS)
```

**Stack:** TypeScript · Node.js 22 · Turborepo · Drizzle · Fastify · Next.js 15 · AWS ECS

**MVP:** Tradovate-only · 1 leader + 10 followers · Bracket copy · Daily loss auto-flatten · Fill audit log

**Next:** Phase 1 — Sprint 0 (repo scaffold + Tradovate API spike)
