# MVP Definition
## Relay — Multi-Account Trade Execution Platform

**Phase:** 0A  
**Version:** 0.1  
**Date:** June 26, 2026  
**Codename:** Relay

---

## 1. MVP Thesis

**Build the smallest product that lets a prop firm trader connect one Tradovate leader account, copy trades to up to 10 follower accounts with per-account risk protection, and trust the system enough to use it with real funded capital.**

The MVP is **not** a Tradesyncer feature-parity launch. It is a **focused wedge**:
- **Platform:** Tradovate API only (covers Apex, Topstep, Tradeify, MFFU, and other Tradovate-routed firms)
- **Differentiation:** Fill-level execution audit + per-account auto-flatten that works on day one
- **Explicitly deferred:** Rithmic, TradingView, journal analytics, API, multi-platform, AI

---

## 2. Target MVP User

**"The 5-Account Tradovate Scaler"**

- Runs 1 leader + 3–10 follower accounts, all Tradovate-routed
- Trades ES/NQ/MES/MNQ on 1–15 minute timeframes (latency tolerant)
- Has blown an account due to manual multi-tab errors or cascade copy without per-account stops
- Will pay $39/mo if sim testing proves reliability in one weekend

**Not MVP user:** Rithmic-only traders, TradingView signal operators, forex prop traders, sub-5ms scalpers.

---

## 3. MVP Goals & Success Criteria

| Goal | Success Metric | Measurement |
|------|----------------|-------------|
| Reliable copy | ≥ 99.5% order replication success in sim | Automated test suite + 10 beta users |
| Risk protection works | 100% of breach tests trigger flatten+lock within 2s | Scripted sim scenarios |
| Fast onboarding | Median time to first sim copy < 15 min | Analytics funnel |
| User trust | ≥ 3 beta users go live with funded accounts | Qualitative + retention |
| Performance | P95 copy latency < 80ms (Tradovate path) | Per-event latency log |

**MVP is successful when:** 10 paying users copy live trades daily for 30 days without a critical incident (unprotected breach, silent copy failure, credential leak).

---

## 4. MVP Feature Set

### 4.1 IN SCOPE ✅

#### Authentication & Billing
- [ ] Email/password signup with email verification
- [ ] 7-day free trial (no credit card)
- [ ] Single paid tier: **Starter @ $39/mo** — 1 leader, up to 10 followers
- [ ] Stripe subscription management (upgrade/cancel)

#### Account Connection
- [ ] Tradovate OAuth/API credential connect
- [ ] Assign role: Leader or Follower
- [ ] Connection status: Connected / Disconnected / Error with last heartbeat
- [ ] Encrypted credential storage (AES-256)
- [ ] Disconnect / reconnect flow

#### Copy Group Configuration
- [ ] One copy group: 1 leader → N followers (N ≤ 10)
- [ ] Enable/disable copying globally (master kill switch)
- [ ] Enable/disable individual followers
- [ ] Per-follower sizing mode:
  - Fixed contracts (e.g., always 1)
  - Ratio multiplier (e.g., 2x, 0.5x)
- [ ] Copy delay setting: immediate (default)

#### Trade Copy Engine
- [ ] Detect leader order submissions and fills via Tradovate API
- [ ] Replicate to enabled followers:
  - Market orders
  - Limit orders
  - Stop orders
  - Bracket orders (entry + stop loss + take profit)
- [ ] Propagate order modifications (price/qty changes)
- [ ] Propagate order cancellations
- [ ] Position reconciliation check every 5s; alert on drift > 0 contracts
- [ ] Skip follower if computed size = 0 (below minimum)

#### Risk Management (Per Follower)
- [ ] Daily loss limit ($) with configurable buffer
- [ ] Action on breach: Auto-flatten all positions + lock follower (stop new copies)
- [ ] Max open contracts per symbol
- [ ] Max total open contracts per account
- [ ] Manual unlock after breach (requires explicit user confirmation)

#### Simulation Mode
- [ ] Toggle: Sim / Live per copy group
- [ ] Sim mode: log copy actions without submitting to broker
- [ ] Sim P&L tracking (based on leader fills + follower sizing rules)
- [ ] "Run sim test" wizard: fire test bracket on leader, verify log output

#### Dashboard & Monitoring
- [ ] Copy group overview: leader, followers, status, sim/live badge
- [ ] Live copy event feed (last 100 events): timestamp, follower, action, result, latency
- [ ] Per-follower: open positions, daily P&L, risk limit % used
- [ ] Per-event fill audit: leader fill price, follower fill price, slippage, latency ms

#### Alerts
- [ ] Email alert on: copy failure, connection lost, daily loss breach, position drift detected
- [ ] In-app notification center

#### Admin & Ops
- [ ] Internal admin panel: user list, connection errors, copy failure rate
- [ ] Structured logging (JSON) for all copy events
- [ ] Health check endpoint + public status page (basic)

---

### 4.2 OUT OF SCOPE ❌ (Post-MVP)

| Feature | Target Phase | Rationale |
|---------|--------------|-----------|
| Rithmic adapter | Phase 2 | Plugin Mode complexity; Tradovate covers largest prop firms |
| TradingView webhooks | Phase 2 | Requires signal parsing + separate leader type |
| NinjaTrader leader bridge | Phase 2 | Requires NT8 integration or third-party relay |
| Multiple copy groups | Phase 2 | Complexity; one group validates core loop |
| Cross-instrument mapping (ES↔MES) | Phase 2 | Requires symbol mapping engine |
| OCO orders (non-bracket) | Phase 2 | Bracket covers 90% of prop use cases |
| Trailing drawdown tracking | Phase 2 | Requires equity high-water mark per account |
| Consistency rule % monitor | Phase 2 | Firm-specific rule engine |
| Pre-trade compliance blocking | Phase 2 | Depends on rule profiles |
| Prop firm pre-built profiles | Phase 2 | Manual config sufficient for MVP beta |
| Session/time lockouts | Phase 2 | Nice-to-have; daily loss is critical path |
| REST API + outbound webhooks | Phase 2 | Beta users don't need automation yet |
| Trading journal / analytics | Phase 2 | Audit log covers MVP; journal is expansion |
| Mobile native app | Phase 3 | Responsive web sufficient |
| Discord/Slack integrations | Phase 2 | Email sufficient for MVP |
| MT4/MT5, cTrader, DXtrade | Phase 3+ | Different market segment |
| AI trade insights | Phase 3 | Differentiation play after core is solid |
| Economic calendar / news blackout | Phase 3 | Thor includes; not MVP-critical |
| Optional local latency bridge | Phase 2 | Cloud-first validation |
| White-label / community plans | Phase 3 | Business model expansion |

---

## 5. User Stories (MVP)

### Epic: Account Setup
```
AS A prop firm trader
I WANT TO connect my Tradovate leader and follower accounts in under 15 minutes
SO THAT I can stop manually copying trades across browser tabs
```
**Acceptance criteria:**
- Connect ≥ 2 accounts without support intervention
- Clear error if credentials invalid
- Sim mode available before any live copy

### Epic: Trade Copy
```
AS A leader account trader
I WANT every market/limit/stop/bracket order to replicate to followers automatically
SO THAT all accounts stay synchronized without manual intervention
```
**Acceptance criteria:**
- Bracket on leader creates matching bracket on followers within 80ms P95
- Modify stop on leader updates follower stops
- Cancel on leader cancels on followers

### Epic: Risk Protection
```
AS A multi-account prop trader
I WANT each follower to auto-flatten and lock when it hits its daily loss limit
SO THAT one bad session doesn't cascade across all my accounts
```
**Acceptance criteria:**
- Breach on follower A does not stop copying on follower B
- Flatten completes within 2s of threshold breach in sim
- User receives email within 30s of breach

### Epic: Trust & Audit
```
AS a funded trader
I WANT to see exactly what was copied, at what price, and how long it took
SO THAT I can diagnose slippage and prove compliance to myself and my firm
```
**Acceptance criteria:**
- Every copy event shows leader price, follower price, delta, latency
- Export last 24h of events (CSV) — Phase 2 if needed; in-app view MVP

---

## 6. Technical Architecture (MVP)

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│  Web Dashboard  │────▶│   Relay API      │────▶│  PostgreSQL     │
│  (React/Next)   │     │   (Auth, Config) │     │  (Users, Config)│
└─────────────────┘     └────────┬─────────┘     └─────────────────┘
                                 │
                    ┌────────────▼────────────┐
                    │   Copy Engine Service   │
                    │   (Event-driven loop)   │
                    └────────────┬────────────┘
                                 │
              ┌──────────────────┼──────────────────┐
              ▼                  ▼                  ▼
     ┌────────────────┐ ┌────────────────┐ ┌────────────────┐
     │ Tradovate WS   │ │ Risk Evaluator │ │ Alert Service  │
     │ Adapter (x N)  │ │ (per follower) │ │ (email)        │
     └────────────────┘ └────────────────┘ └────────────────┘
              │
              ▼
     ┌────────────────┐
     │ Tradovate API  │
     │ (Leader +      │
     │  Followers)    │
     └────────────────┘
```

### Core Components
1. **Tradovate Adapter** — WebSocket for leader events; REST for follower order submission
2. **Copy Engine** — Idempotent event processor; maps leader orders → follower orders
3. **Risk Evaluator** — Pre-copy checks (contract caps) + post-fill P&L monitor (daily loss)
4. **Reconciliation Worker** — Periodic position compare; drift alerts
5. **Audit Log** — Append-only event store for every copy attempt

### Infrastructure (MVP)
- Cloud: AWS or GCP (single region, us-east for CME proximity)
- Containerized services (Docker + ECS/Cloud Run)
- Managed PostgreSQL + Redis (pub/sub for events)
- Secrets: AWS Secrets Manager or GCP Secret Manager

---

## 7. MVP Milestones & Timeline

| Milestone | Duration | Deliverable |
|-----------|----------|-------------|
| **M0: Foundation** | Weeks 1–2 | Auth, billing, Tradovate OAuth POC (connect + read positions) |
| **M1: Copy Engine** | Weeks 3–5 | Leader detection → follower market/limit/stop copy in sim |
| **M2: Brackets + Risk** | Weeks 6–7 | Bracket replication; daily loss flatten+lock |
| **M3: Dashboard** | Weeks 8–9 | Web UI, event feed, fill audit, email alerts |
| **M4: Beta** | Weeks 10–11 | 10 beta users, sim + limited live, bug fixes |
| **M5: Launch** | Week 12 | Public Starter tier, docs, status page |

**Total MVP timeline:** ~12 weeks (3 months) with 2 engineers + 1 part-time designer

---

## 8. MVP Non-Goals

- Feature parity with Tradesyncer, Thor, or Copilink
- Support for every prop firm on day one (document Tradovate-routed firms only)
- Sub-10ms latency optimization
- Mobile app store presence
- SOC 2 certification (begin readiness, don't block launch)
- Multi-region deployment

---

## 9. Future Features Roadmap

### Phase 2 — "Prop Firm Native" (Months 4–6)
**Theme:** Close compliance gap with Copilink; expand platform reach

| Feature | User Value |
|---------|------------|
| Rithmic adapter | Earn2Trade, Rithmic-routed Apex/MFFU accounts |
| TradingView webhook leader | Signal traders without NT8 |
| Cross-instrument mapping (ES↔MES) | Correct sizing across account types |
| Prop firm rule profiles (Apex, Topstep, Tradeify, MFFU) | One-click rule setup |
| Trailing drawdown + consistency rule monitor | Payout-stage account protection |
| Pre-trade compliance blocking | Prevent violations before submission |
| Session lockouts + auto end-of-day flatten | Discipline automation |
| Multiple copy groups | Separate strategies per group |
| REST API + outbound webhooks | Integrations, Discord bots, custom dashboards |
| CSV/JSON export + basic journal | Performance tracking |

**Pricing addition:** Pro tier @ $79/mo (30 followers, Rithmic, webhooks)

### Phase 3 — "Scale & Intelligence" (Months 7–12)
**Theme:** Match Thor breadth; add intelligence layer

| Feature | User Value |
|---------|------------|
| NinjaTrader leader bridge | Native NT8 users as leaders |
| ProjectX / TopstepX / DxFeed | Expanding firm coverage |
| Optional local latency bridge | Sub-10ms for latency-sensitive users |
| Full trading journal + analytics | Replace Tradervue/spreadsheet workflows |
| AI trade insights (pattern detection, sizing suggestions) | Actionable improvement loop |
| Economic calendar + news blackout | Automated volatility protection |
| Discord/Slack native integrations | Community trader workflows |
| Scale tier: unlimited followers @ $129/mo | Compete with Thor on scale economics |
| White-label for trading communities | B2B revenue stream |

### Phase 4 — "Cross-Asset" (Year 2+)
**Theme:** Expand TAM beyond futures prop

| Feature | User Value |
|---------|------------|
| MT4/MT5, cTrader, DXtrade, TradeLocker | Forex prop (FTMO, E8, etc.) |
| Unified dashboard across asset classes | One control plane for mixed books |
| Strategy marketplace / signal provider tools | Platform network effects |
| Enterprise / prop firm desk licensing | B2B at scale |

---

## 10. Differentiators Summary

### MVP Differentiators (Ship Day 1)
1. **Fill-level execution audit** — Every copy logged with leader vs. follower price, slippage, latency
2. **Per-account breach isolation** — Flatten+lock one account; others keep running
3. **Sim-first onboarding** — Guided test before live capital
4. **Honest scope** — Tradovate-only, done well, vs. overpromised multi-platform

### Roadmap Differentiators (Build Toward)
5. **Prop firm rule engine** — Copilink-grade compliance in the cloud
6. **Pre-trade blocking** — Trada-style prevention, not just reaction
7. **Flat scale pricing** — Thor-like economics without sacrificing compliance
8. **Open event API** — Automation-friendly from Phase 2

---

## 11. MVP Risks & Mitigations

| Risk | Likelihood | Mitigation |
|------|------------|------------|
| Tradovate API rate limits at 10 followers | Medium | Connection pooling; batch where possible; load test early |
| Bracket order edge cases (partial fills) | High | Extensive sim test matrix; reconciliation worker |
| Beta users expect Rithmic on day one | High | Clear marketing: "Tradovate-first"; waitlist for Rithmic |
| Copy failure during fast market | Medium | Market-only mode; aggressive alerting; pause follower on retry exhaustion |
| Prop firm ToS ambiguity | Medium | Publish compatibility list; user acknowledgment checkbox |

---

## 12. Launch Checklist

- [ ] Tradovate API production credentials approved
- [ ] 50+ sim test scenarios passing (market, limit, stop, bracket, modify, cancel)
- [ ] 10 breach scenarios passing (daily loss, contract cap)
- [ ] Security review: credential encryption, auth, SQL injection, rate limiting
- [ ] Privacy policy + Terms of Service + risk disclaimers
- [ ] Help docs: setup guide, supported firms, FAQ
- [ ] Status page live
- [ ] Beta feedback incorporated; 0 P0 bugs open
- [ ] Stripe live mode tested

---

## 13. Document Index

| Document | Purpose |
|----------|---------|
| [PRD.md](./PRD.md) | Full product requirements and vision |
| [COMPETITOR_ANALYSIS.md](./COMPETITOR_ANALYSIS.md) | Market and competitor deep dive |
| [FEATURE_MATRIX.md](./FEATURE_MATRIX.md) | Side-by-side feature comparison |
| **MVP_DEFINITION.md** (this doc) | Scope, timeline, and roadmap |

---

## Appendix: MVP vs. Tradesyncer Feature Overlap

| Tradesyncer Feature | Relay MVP | Notes |
|-------------------|-----------|-------|
| Cloud 24/7 | ✅ | Parity |
| Tradovate support | ✅ | Parity |
| Rithmic support | ❌ Phase 2 | Intentional cut |
| TradingView leader | ❌ Phase 2 | Intentional cut |
| Bracket/OCO copy | ✅ Bracket only | OCO Phase 2 |
| Per-follower sizing | ✅ | Parity |
| Daily loss lockout | ✅ | Parity (must work day 1) |
| Trading journal | ❌ Phase 2 | Audit log in MVP |
| Multiple copy groups | ❌ Phase 2 | Single group MVP |
| Economic calendar | ❌ Phase 3 | Not critical |
| Mobile app | ⚠️ Responsive web | Native Phase 3 |
| Cross-broker leader→follower | ⚠️ Tradovate→Tradovate | Cross-broker Phase 2 |
| Pricing | $39 vs $49 | Undercut entry |

**MVP captures ~60% of Tradesyncer's perceived value for Tradovate-only users, with stronger audit transparency and clearer scope.**
