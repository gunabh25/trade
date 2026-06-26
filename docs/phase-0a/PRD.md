# Product Requirements Document (PRD)
## Relay — Multi-Account Trade Execution Platform

**Phase:** 0A — Product Research  
**Version:** 0.1 (Draft)  
**Date:** June 26, 2026  
**Status:** Research Complete → MVP Scoping

---

## 1. Executive Summary

**Relay** is a cloud-native trade execution and account orchestration platform for futures traders—primarily prop firm traders managing multiple funded and evaluation accounts. The product synchronizes trades from a single **leader account** to multiple **follower accounts** across brokers and platforms, with per-account risk controls and execution auditability built in from day one.

This PRD is informed by analysis of market leaders including [Tradesyncer](https://tradesyncer.com/), [Thor](https://thortradecopier.com/), [Copilink](https://copilink.com/trade-copier), [Lune Trade Copier](https://lunefi.com/), [Replikanto](https://flowbots.com/), [Trada](https://trada.io/), and [MimikTrader](https://mimiktrader.com/). The goal is **not to clone Tradesyncer**, but to learn from category-defining functionality and build a differentiated product that solves the same core problem with clearer trade-offs.

### Problem Statement

Prop firm traders scaling beyond 2–3 accounts face a structural execution problem:

- Manual multi-tab order entry causes missed fills, asymmetric positions, and reconciliation nightmares
- One mistake on the leader account is amplified across every follower
- Each account has different size, drawdown rules, and firm-specific compliance requirements
- Existing tools force a painful trade-off: **ultra-low latency (local/VPS)** vs. **always-on cloud convenience**

### Product Vision

Give serious futures traders a single control plane to execute once, replicate everywhere, and protect each account independently—without sacrificing transparency, compliance, or reliability.

### Success Metrics (12-month targets post-launch)

| Metric | Target |
|--------|--------|
| Median copy latency (Tradovate API path) | < 50ms P95 |
| Position sync accuracy | > 99.9% fill reconciliation |
| Accounts protected from cascade breach | Per-account lockout within 1 tick of threshold |
| Time to first copied trade (onboarding) | < 15 minutes |
| Monthly active accounts (platform-wide) | 5,000+ |
| Net Promoter Score | ≥ 45 |

---

## 2. Target Users & Personas

### Primary Persona: The Prop Firm Scaler
- **Profile:** Day trader, 3–40 funded/eval accounts across Apex, Topstep, Tradeify, MFFU, etc.
- **Platforms:** NinjaTrader + Tradovate API and/or Rithmic
- **Pain:** Cannot manually fire entries across 10 tabs during volatile opens
- **Jobs to be done:** Copy leader fills with per-account sizing; auto-lock accounts before firm breach; track P&L across accounts

### Secondary Persona: The Signal Operator
- **Profile:** Uses TradingView alerts or a systematic leader account
- **Pain:** Needs reliable webhook → multi-broker execution without maintaining a VPS
- **Jobs to be done:** Route signals to followers with sizing rules and failure alerts

### Tertiary Persona: The Risk-Conscious Funded Trader
- **Profile:** 1 leader + 2–5 followers, highly rule-aware
- **Pain:** Copiers mirror trades but don't understand prop firm rulebooks
- **Jobs to be done:** Pre-trade compliance checks, consistency rule monitoring, audit trail for disputes

### Anti-Persona (Out of Scope for MVP)
- Ultra-HFT scalpers requiring sub-5ms local execution
- Forex-only traders on MT4/MT5 without futures accounts
- Discretionary single-account retail traders

---

## 3. Market Context

### Category Definition
Trade copiers sit between **broker platforms** (Tradovate, Rithmic, NinjaTrader) and **prop firms**. They are execution middleware—not brokers, not evaluators, not signal vendors.

### Market Drivers (2026)
1. **Prop firm proliferation** — traders routinely stack 5–20+ accounts
2. **Platform fragmentation** — Tradovate vs. Rithmic vs. ProjectX across firms
3. **Rule complexity** — trailing drawdown, consistency %, daily loss, contract caps vary by firm
4. **Cloud expectation** — traders reject VPS babysitting; want browser/mobile control
5. **Pricing fatigue** — per-connection/per-account tiers create unpredictable costs at scale

### Competitive Landscape Summary
See [COMPETITOR_ANALYSIS.md](./COMPETITOR_ANALYSIS.md) and [FEATURE_MATRIX.md](./FEATURE_MATRIX.md).

**Key insight:** The market splits into three archetypes:
- **Cloud convenience** (Tradesyncer, Lune, Thor cloud) — 40–100ms+ latency, no VPS
- **Local speed** (Copilink, Replikanto, ETP, Tradecopia) — 1–15ms, requires NT8/VPS
- **Compliance depth** (Copilink, Trada, MimikTrader) — prop-firm rule enforcement as core value

---

## 4. Product Principles

1. **Per-account sovereignty** — Risk actions on one follower never affect others
2. **Leader is source of truth** — All replication derives from leader fills/orders
3. **Fail safe, not fail silent** — Mismatch, timeout, or breach → alert + corrective action
4. **Prop-firm literate** — Rules are first-class data, not user-configured hacks
5. **Transparent execution** — Every copy attempt logged with latency, fill price, and delta
6. **Progressive disclosure** — Simple defaults for beginners; advanced controls for scalers

---

## 5. Functional Requirements

### 5.1 Account Connection & Management
| ID | Requirement | Priority |
|----|-------------|----------|
| AC-1 | OAuth/API credential connect for Tradovate accounts | P0 |
| AC-2 | Rithmic connection via supported adapter (Plugin Mode compatible) | P1 |
| AC-3 | Leader/follower role assignment per account | P0 |
| AC-4 | Account health dashboard (connected, stale, error) | P0 |
| AC-5 | Encrypted credential vault (AES-256 at rest) | P0 |
| AC-6 | NinjaTrader as leader signal source (Phase 2) | P2 |
| AC-7 | TradingView webhook as leader input | P1 |

### 5.2 Trade Copy Engine
| ID | Requirement | Priority |
|----|-------------|----------|
| CP-1 | Real-time replication of market, limit, stop orders | P0 |
| CP-2 | Bracket order replication (entry + SL + TP) | P0 |
| CP-3 | Order modify and cancel propagation | P0 |
| CP-4 | Per-follower sizing: fixed, ratio, balance-proportional | P0 |
| CP-5 | Cross-instrument mapping (ES↔MES, NQ↔MNQ) | P1 |
| CP-6 | Market-only execution mode for followers | P1 |
| CP-7 | Copy groups (multiple leader→follower sets) | P2 |
| CP-8 | Position reconciliation loop (detect/fix drift) | P0 |

### 5.3 Risk Management
| ID | Requirement | Priority |
|----|-------------|----------|
| RM-1 | Per-account daily loss limit with auto-flatten + lock | P0 |
| RM-2 | Per-account max contract / symbol exposure caps | P0 |
| RM-3 | Session/time-based trading lockouts | P1 |
| RM-4 | Trailing drawdown monitoring with alerts | P1 |
| RM-5 | Prop firm rule profiles (Apex, Topstep, etc.) pre-configured | P1 |
| RM-6 | Consistency rule % tracking with warnings | P2 |
| RM-7 | Pre-trade block (reject copy if rule would be violated) | P2 |
| RM-8 | Buffer below firm limits (configurable 0.3–0.5%) | P0 |

### 5.4 Monitoring, Alerts & Journal
| ID | Requirement | Priority |
|----|-------------|----------|
| MJ-1 | Real-time copy status per follower (success/fail/skip) | P0 |
| MJ-2 | Push/email/Discord alerts on copy failure or breach | P0 |
| MJ-3 | Unified trade log across all accounts | P1 |
| MJ-4 | Per-account P&L and open position view | P0 |
| MJ-5 | Execution latency metrics per copy event | P1 |
| MJ-6 | Exportable audit log (CSV/JSON) | P2 |

### 5.5 Platform & Access
| ID | Requirement | Priority |
|----|-------------|----------|
| PL-1 | Web dashboard (desktop + mobile responsive) | P0 |
| PL-2 | 24/7 cloud operation (no user machine required) | P0 |
| PL-3 | Sim/demo mode for setup validation | P0 |
| PL-4 | REST API for account status and copy control | P2 |
| PL-5 | Webhook outbound events (copy success/fail/breach) | P2 |

---

## 6. Non-Functional Requirements

| Category | Requirement |
|----------|-------------|
| **Latency** | P50 < 30ms, P95 < 80ms for Tradovate path under normal conditions |
| **Availability** | 99.9% uptime for copy engine; status page public |
| **Security** | SOC 2 roadmap; GDPR/CCPA compliant data handling; no plaintext credentials |
| **Scalability** | Support 50 followers per copy group at launch; 200+ roadmap |
| **Compliance** | Clear disclaimers; no custody of funds; broker ToS alignment |
| **Support** | In-app help, setup wizard, email support with < 24h response |

---

## 7. User Flows

### 7.1 Onboarding (Happy Path)
```
Sign up → Choose plan → Connect leader (Tradovate) → Connect followers →
Configure sizing per follower → Enable sim test → Run test trade →
Set daily loss limits → Go live → Monitor dashboard
```
**Target:** < 15 minutes to first successful sim copy

### 7.2 Live Copy Session
```
Trader executes on leader → Relay detects fill →
For each follower: check risk rules → size order → submit →
Confirm fill → log event → update dashboard
```
If any follower fails: alert user; optionally pause that follower only

### 7.3 Risk Breach
```
Follower P&L hits daily loss threshold → Auto-flatten open positions →
Lock follower (stop new copies) → Alert user → Other followers continue
```

---

## 8. Differentiators

Relay enters a crowded market. Differentiation must be **defensible and user-visible**:

| Differentiator | Why It Matters | Competitor Gap |
|----------------|----------------|----------------|
| **Prop Firm Rule Engine** | Pre-loaded firm profiles (drawdown type, consistency %, contract caps) reduce setup errors | Tradesyncer has basic caps; Copilink has depth but is NT8-only |
| **Hybrid Latency Option** | Optional lightweight local bridge for sub-10ms when needed, cloud dashboard always on | Cloud players can't match local; local players need VPS |
| **Execution Transparency** | Fill-level audit: leader price vs. follower price, slippage, latency per event | Most copiers show status, not forensic detail |
| **Flat, Predictable Pricing** | Unlimited followers at one tier (like Thor $39/mo model) | Tradesyncer tiers by connections/accounts |
| **Per-Account Pre-Trade Compliance** | Block violating copies before submission, not just post-breach flatten | Trada has this for forex; futures cloud copiers mostly reactive |
| **Open Event API** | Webhooks + REST for journals, Discord bots, custom dashboards | Thor has full API; Tradesyncer limited |

**Primary positioning statement:**
> *"The prop-firm-native trade copier—copy once, protect every account, see every fill."*

---

## 9. MVP Scope

See [MVP_DEFINITION.md](./MVP_DEFINITION.md) for full detail.

**In MVP:**
- Tradovate-only (covers Apex, Topstep, Tradeify, MFFU via NT/Tradovate API)
- Leader + up to 10 followers
- Core copy (market/limit/stop/bracket)
- Per-account daily loss + contract caps + auto-flatten
- Web dashboard + alerts
- Sim mode

**Post-MVP (Phase 2+):**
- Rithmic, TradingView webhooks, NinjaTrader leader
- Consistency rule engine, trailing drawdown
- Trading journal analytics, API/webhooks
- Mobile app, multi copy groups, forex platforms

---

## 10. Pricing Strategy (Draft)

| Plan | Price | Includes |
|------|-------|----------|
| **Trial** | Free 7 days | Full features, 5 followers max |
| **Starter** | $39/mo | 1 leader, 10 followers, core risk |
| **Pro** | $79/mo | 1 leader, 30 followers, Rithmic + webhooks |
| **Scale** | $129/mo | Unlimited followers, API, priority support |

**Rationale:** Undercut Tradesyncer Basic ($49) while matching Thor/Lune flat-value perception. No per-connection tax.

---

## 11. Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Broker API changes / rate limits | Copy failures | Adapter abstraction; connection pooling; retry with backoff |
| Prop firm ToS restrictions on third-party tools | User account termination | Clear compatibility docs; sim-first onboarding |
| Latency during news events | Slippage, rule breaches | Market-only mode; pre-news lockout; latency SLO monitoring |
| Security breach of credentials | Catastrophic trust loss | Vault encryption, minimal credential scope, audit logging |
| Incumbent network effects (Tradesyncer brand) | Slow adoption | Niche on compliance + transparency; prop firm partnerships |

---

## 12. Open Questions

1. **Legal:** Prop firm explicit allowlist vs. generic "user responsibility" disclaimer?
2. **Architecture:** Build cloud-only MVP first, or hybrid local agent from start?
3. **Rithmic:** MVP+1 or co-launch given Plugin Mode complexity?
4. **Revenue:** Flat subscription only, or optional white-label for trading communities?
5. **Journal:** Build in-house vs. integrate (e.g., Tradervue API)?

---

## 13. Appendix

### Reference Platforms Analyzed
- [Tradesyncer](https://tradesyncer.com/) — Cloud futures copier, journal, risk caps
- [Thor](https://thortradecopier.com/) — Server-based, 11+ platforms, flat $39/mo, API
- [Lune Trade Copier](https://lunefi.com/) — Cloud, 5–10ms, 100+ prop firms
- [Copilink](https://copilink.com/trade-copier) — NT8 local, prop rule engine, ~1.6ms
- [Replikanto](https://flowbots.com/) — NT8 lifetime license, Follower Guard
- [Tradecopia](https://tradecopia.com/) — Local desktop, unlimited accounts
- [Trada](https://trada.io/) — Cross forex/futures, compliance blocking
- [MimikTrader](https://mimiktrader.com/) — Per-tick risk enforcement
- Tradovate Group Trade — Free native multi-account (same broker only)

### Related Documents
- [COMPETITOR_ANALYSIS.md](./COMPETITOR_ANALYSIS.md)
- [FEATURE_MATRIX.md](./FEATURE_MATRIX.md)
- [MVP_DEFINITION.md](./MVP_DEFINITION.md)
