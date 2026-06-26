# Software Requirements Specification (SRS)
## Relay — Multi-Account Trade Execution Platform

**Document ID:** RELAY-SRS-001  
**Version:** 1.0  
**Date:** June 26, 2026  
**Phase:** 0B — System Architecture  
**Status:** Approved for Implementation  
**References:** [PRD](../phase-0a/PRD.md), [MVP Definition](../phase-0a/MVP_DEFINITION.md)

---

## 1. Introduction

### 1.1 Purpose
This Software Requirements Specification defines the functional and non-functional requirements for Relay MVP v1.0 — a cloud-native trade copier for Tradovate-routed prop firm accounts. It is the authoritative input for system design, implementation, and acceptance testing.

### 1.2 Scope
Relay MVP provides:
- User authentication, billing, and account management
- Tradovate broker account connection (leader + followers)
- Real-time trade replication with per-follower sizing
- Per-account risk management (daily loss, contract caps)
- Simulation mode, execution audit, and alerting

**Out of scope:** Rithmic, TradingView, public API, multi copy groups, trading journal analytics.

### 1.3 Definitions

| Term | Definition |
|------|------------|
| **Leader** | Source account whose orders/fills drive replication |
| **Follower** | Target account that receives copied orders |
| **Copy Group** | One leader linked to N followers with shared config |
| **Copy Event** | A single replication attempt (order submit, modify, cancel) |
| **Sim Mode** | Copy logic runs without broker submission |
| **Flatten** | Close all open positions on an account |
| **Lock** | Stop new copies to a follower until manual unlock |
| **Drift** | Position mismatch between expected and actual follower state |

### 1.4 References
- [Tradovate API](https://api.tradovate.com/)
- [Tradovate Partner API — Auth](https://partner.tradovate.com/overview/quick-setup/auth-overview)
- [Tradovate WebSocket Conformance](https://partner.tradovate.com/overview/conformance-testing/stage-2-websocket-management)
- Phase 0A deliverables in `docs/phase-0a/`

---

## 2. Overall Description

### 2.1 Product Perspective
Relay is a standalone SaaS platform. External system interfaces:

| System | Interface | Direction |
|--------|-----------|-----------|
| Tradovate API | REST + WebSocket | Bidirectional |
| Stripe | REST + Webhooks | Bidirectional |
| Email provider (Resend) | REST | Outbound |
| User browser | HTTPS + SSE | Bidirectional |

### 2.2 User Classes

| Class | Description | Access |
|-------|-------------|--------|
| **Trader** | End user managing copy groups | Dashboard, own data only |
| **Admin** | Internal operator | Admin panel, all users (read + support actions) |
| **System** | Background workers | Internal services only |

### 2.3 Operating Environment
- **Production:** AWS `us-east-1` (CME proximity)
- **Staging:** AWS `us-east-1` (Tradovate demo/staging endpoints)
- **Development:** Local Docker Compose + Tradovate demo API
- **Client:** Modern browsers (Chrome, Firefox, Safari, Edge — last 2 versions)

### 2.4 Design Constraints
- Tradovate access tokens expire after 90 minutes; refresh at 85 minutes
- WebSocket heartbeat required every 2.5 seconds per [Tradovate protocol](https://api.tradovate.com/)
- MVP limited to 1 copy group and 10 followers per user
- Broker credentials must never be stored in plaintext
- All copy events must be append-only (no deletion)

### 2.5 Assumptions
- Users have valid Tradovate-routed prop firm accounts with API access enabled
- Users accept responsibility for prop firm ToS compliance
- Tradovate demo API available for staging/sim testing
- Stripe available in target markets (US, CA initially)

---

## 3. Functional Requirements

### 3.1 User Management (UM)

| ID | Requirement | Priority |
|----|-------------|----------|
| UM-001 | System shall allow registration with email and password (min 12 chars) | P0 |
| UM-002 | System shall send email verification before full access | P0 |
| UM-003 | System shall support password reset via email link (expires 1h) | P0 |
| UM-004 | System shall support session-based auth with HTTP-only secure cookies | P0 |
| UM-005 | System shall enforce rate limiting on auth endpoints (5 attempts/min/IP) | P0 |
| UM-006 | System shall allow account deletion with 30-day credential purge | P1 |

### 3.2 Subscription & Billing (SB)

| ID | Requirement | Priority |
|----|-------------|----------|
| SB-001 | System shall offer 7-day free trial without credit card | P0 |
| SB-002 | System shall integrate Stripe Checkout for Starter plan ($39/mo) | P0 |
| SB-003 | System shall enforce plan limits: 1 leader, 10 followers max | P0 |
| SB-004 | System shall handle Stripe webhooks: subscription created/updated/canceled | P0 |
| SB-005 | System shall restrict live copying when subscription inactive | P0 |
| SB-006 | System shall allow sim mode during trial regardless of payment status | P0 |

### 3.3 Broker Account Connection (BA)

| ID | Requirement | Priority |
|----|-------------|----------|
| BA-001 | System shall connect Tradovate accounts via OAuth or API credentials | P0 |
| BA-002 | System shall assign each account role: `leader` or `follower` | P0 |
| BA-003 | System shall display connection status: `connected`, `disconnected`, `error` | P0 |
| BA-004 | System shall store credentials encrypted at rest (AES-256-GCM) | P0 |
| BA-005 | System shall refresh Tradovate tokens automatically every 85 minutes | P0 |
| BA-006 | System shall maintain one WebSocket connection per connected account in engine | P0 |
| BA-007 | System shall reconnect WebSocket with exponential backoff on disconnect | P0 |
| BA-008 | System shall allow user to disconnect account (revoke + delete credentials) | P0 |
| BA-009 | System shall reject duplicate account binding across users | P0 |

### 3.4 Copy Group Configuration (CG)

| ID | Requirement | Priority |
|----|-------------|----------|
| CG-001 | System shall support one copy group per user (MVP) | P0 |
| CG-002 | System shall require exactly one leader and 1–10 followers | P0 |
| CG-003 | System shall provide global copy enable/disable (master kill switch) | P0 |
| CG-004 | System shall allow per-follower enable/disable | P0 |
| CG-005 | System shall support sizing modes: `fixed` (contracts) and `ratio` (multiplier) | P0 |
| CG-006 | System shall compute follower size as `round(leader_qty × ratio)` or fixed value | P0 |
| CG-007 | System shall skip follower when computed size < 1 contract | P0 |
| CG-008 | System shall support mode toggle: `sim` or `live` | P0 |
| CG-009 | System shall prevent live mode activation without ≥1 successful sim test | P0 |

### 3.5 Trade Copy Engine (CE)

| ID | Requirement | Priority |
|----|-------------|----------|
| CE-001 | System shall subscribe to leader order and fill events via Tradovate WebSocket | P0 |
| CE-002 | System shall replicate market orders to enabled followers | P0 |
| CE-003 | System shall replicate limit orders with same limit price | P0 |
| CE-004 | System shall replicate stop orders with same stop price | P0 |
| CE-005 | System shall replicate bracket orders (entry + SL + TP) as linked group | P0 |
| CE-006 | System shall propagate order modifications (price, qty) to mapped follower orders | P0 |
| CE-007 | System shall propagate order cancellations to mapped follower orders | P0 |
| CE-008 | System shall maintain leader→follower order ID mapping for lifecycle tracking | P0 |
| CE-009 | System shall process copy events idempotently (dedupe by leader event ID) | P0 |
| CE-010 | System shall record latency_ms from leader event receipt to follower submit ack | P0 |
| CE-011 | In sim mode, system shall log intended action without broker submission | P0 |
| CE-012 | System shall retry failed follower submits up to 3 times with backoff | P0 |
| CE-013 | System shall pause follower after 3 consecutive copy failures | P0 |
| CE-014 | System shall alert user on copy failure within 30 seconds | P0 |

### 3.6 Risk Management (RM)

| ID | Requirement | Priority |
|----|-------------|----------|
| RM-001 | System shall enforce per-follower daily loss limit (USD, configurable) | P0 |
| RM-002 | On daily loss breach: flatten all positions + lock follower | P0 |
| RM-003 | Breach on follower A shall not affect copying on follower B | P0 |
| RM-004 | System shall enforce max open contracts per symbol per follower | P0 |
| RM-005 | System shall enforce max total open contracts per follower | P0 |
| RM-006 | System shall block new copies when follower is locked | P0 |
| RM-007 | System shall require explicit user confirmation to unlock follower | P0 |
| RM-008 | System shall run pre-copy risk check before every follower submit | P0 |
| RM-009 | Daily P&L shall reset at configurable session boundary (default 6 PM ET) | P0 |
| RM-010 | Flatten shall complete within 2 seconds of breach detection (P95) | P0 |

### 3.7 Reconciliation (RC)

| ID | Requirement | Priority |
|----|-------------|----------|
| RC-001 | System shall compare leader vs. follower positions every 5 seconds | P0 |
| RC-002 | System shall alert on drift > 0 contracts for any enabled follower | P0 |
| RC-003 | System shall log drift events with expected vs. actual position | P0 |
| RC-004 | System shall not auto-correct drift in MVP (alert only) | P0 |

### 3.8 Monitoring & Audit (MA)

| ID | Requirement | Priority |
|----|-------------|----------|
| MA-001 | System shall maintain append-only copy event log | P0 |
| MA-002 | Each event shall record: timestamp, leader_order_id, follower_id, action, result, leader_price, follower_price, slippage, latency_ms | P0 |
| MA-003 | Dashboard shall display last 100 copy events in real time (SSE) | P0 |
| MA-004 | Dashboard shall show per-follower: positions, daily P&L, risk limit usage % | P0 |
| MA-005 | System shall expose `/health` and `/ready` endpoints | P0 |
| MA-006 | Admin shall view aggregate copy failure rate per user | P1 |

### 3.9 Notifications (NT)

| ID | Requirement | Priority |
|----|-------------|----------|
| NT-001 | System shall send email on: copy failure, connection lost, daily loss breach, position drift | P0 |
| NT-002 | System shall display in-app notifications with read/unread state | P0 |
| NT-003 | System shall dedupe alerts (same type + follower) within 5 minutes | P1 |

### 3.10 Simulation & Onboarding (SO)

| ID | Requirement | Priority |
|----|-------------|----------|
| SO-001 | System shall provide sim test wizard with checklist steps | P0 |
| SO-002 | Sim test shall verify leader event detection and follower log output | P0 |
| SO-003 | System shall track sim P&L based on leader fills × follower sizing | P1 |
| SO-004 | System shall mark copy group `sim_validated` after successful wizard | P0 |

---

## 4. External Interface Requirements

### 4.1 User Interface
- Responsive web dashboard (desktop + mobile)
- Pages: Login, Register, Dashboard, Accounts, Copy Group, Events, Settings, Billing
- Real-time event feed via Server-Sent Events (SSE)
- WCAG 2.1 AA target for core flows (Phase 2 full audit)

### 4.2 Hardware Interfaces
None (cloud SaaS).

### 4.3 Software Interfaces

#### Tradovate API
| Endpoint Type | Usage |
|---------------|-------|
| REST `POST /auth/accesstokenrequest` | Token acquisition |
| REST `/order/*` | Order placement (fallback) |
| WebSocket `wss://*.tradovateapi.com/v1/websocket` | Real-time events + order submit |
| WebSocket `authorize` | Session auth |
| WebSocket `user/syncrequest` | Entity subscriptions |
| Heartbeat `[]` every 2.5s | Connection keepalive |

#### Stripe
- Checkout Session creation
- Customer Portal
- Webhooks: `customer.subscription.*`, `invoice.payment_failed`

#### Email (Resend)
- Transactional templates: verify, reset, alert

### 4.4 Communication Interfaces
- HTTPS TLS 1.2+ for all external traffic
- Internal service communication via Redis (TLS in prod)
- No public WebSocket to browser in MVP (SSE sufficient)

---

## 5. Non-Functional Requirements

### 5.1 Performance

| Metric | Requirement |
|--------|-------------|
| Copy latency P50 | < 30ms (leader event → follower submit ack) |
| Copy latency P95 | < 80ms |
| API response P95 | < 200ms (excluding Tradovate proxy calls) |
| Dashboard SSE delivery | < 500ms from event persist |
| Concurrent users (MVP) | 100 users, 500 connected accounts |
| Copy throughput | 50 copy events/sec platform-wide |

### 5.2 Availability
- Copy engine uptime: 99.9% (excluding planned maintenance)
- Planned maintenance window: Sundays 2–4 AM ET with 48h notice
- Graceful degradation: dashboard available even if one user's engine shard fails

### 5.3 Security
See [SECURITY_PLAN.md](./SECURITY_PLAN.md). Summary:
- Encryption at rest and in transit
- RBAC (trader vs. admin)
- Audit logging for admin actions
- No broker credentials in logs

### 5.4 Scalability
- Engine horizontally shardable by `copy_group_id` (Phase 2)
- MVP: single engine instance sufficient for 100 users
- PostgreSQL read replica ready in schema design (not required MVP)

### 5.5 Maintainability
- Monorepo with shared packages
- 80% unit test coverage on `copy-core` and `risk` packages
- Structured JSON logging with correlation IDs
- Database migrations via Drizzle Kit

### 5.6 Compliance & Legal
- GDPR/CCPA: data export and deletion endpoints (Phase 2 full; MVP deletion flow)
- Risk disclaimers at signup and before live mode
- No custody of user funds

---

## 6. Data Requirements

### 6.1 Data Retention
| Data Type | Retention |
|-----------|-----------|
| Copy events (audit log) | 2 years |
| User credentials (encrypted) | Until disconnect + 30 days |
| Application logs | 90 days |
| Stripe billing records | Per Stripe/legal (7 years) |

### 6.2 Data Integrity
- Copy events: append-only, no UPDATE/DELETE
- Foreign key constraints on all relational data
- Unique constraints on broker account external IDs per environment

---

## 7. Acceptance Criteria (MVP Release)

| # | Criterion | Verification |
|---|-----------|--------------|
| AC-1 | User completes signup → connect 2 accounts → sim copy in < 15 min | Usability test (n=5) |
| AC-2 | 99.5% copy success in automated sim test suite (50 scenarios) | CI integration tests |
| AC-3 | Daily loss breach triggers flatten+lock in 100% of 10 test scenarios | Automated risk tests |
| AC-4 | P95 copy latency < 80ms in staging load test | k6 benchmark |
| AC-5 | Zero plaintext credentials in logs (automated scan) | Security test |
| AC-6 | 10 beta users run live copy for 30 days without P0 incident | Beta program |

---

## 8. Traceability Matrix

| PRD Requirement | SRS IDs |
|-----------------|---------|
| AC-1 Tradovate connect | BA-001–009 |
| CP-1–8 Copy engine | CE-001–014 |
| RM-1–8 Risk | RM-001–010 |
| MJ-1–5 Monitoring | MA-001–006, RC-001–004 |
| PL-1–3 Platform | UM, SB, MA-005 |
| Sim mode | SO-001–004, CG-008–009 |

---

## Related Documents
- [HIGH_LEVEL_ARCHITECTURE.md](./HIGH_LEVEL_ARCHITECTURE.md)
- [LOW_LEVEL_DESIGN.md](./LOW_LEVEL_DESIGN.md)
- [TECHNOLOGY_DECISIONS.md](./TECHNOLOGY_DECISIONS.md)
- [SECURITY_PLAN.md](./SECURITY_PLAN.md)
