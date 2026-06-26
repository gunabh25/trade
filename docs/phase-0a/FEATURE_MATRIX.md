# Feature Comparison Matrix
## Phase 0A — Trade Copier & Multi-Account Execution Platforms

**Date:** June 26, 2026  
**Legend:** ✅ Full support · ⚠️ Partial/Limited · ❌ Not supported · 🔜 Planned · — Unknown/Not public

**Working product codename:** Relay (proposed)

---

## 1. Core Platform Comparison

| Feature | **Relay** (Proposed) | Tradesyncer | Thor | Lune | Copilink | Replikanto | Tradecopia | Trada | MimikTrader |
|---------|---------------------|-------------|------|------|----------|------------|------------|-------|-------------|
| **Architecture** | Cloud (+ optional bridge) | Cloud | Server cloud | Cloud | Local NT8 | Local NT8 | Local desktop | Cloud | Cloud |
| **VPS required** | ❌ | ❌ | ❌ | ❌ | ⚠️ For 24/7 | ⚠️ For 24/7 | ⚠️ For 24/7 | ❌ | ❌ |
| **Web dashboard** | ✅ | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ | ✅ | ✅ |
| **Mobile access** | ✅ (responsive) | ✅ | ⚠️ | ✅ | ❌ | ❌ | ❌ | ✅ | ⚠️ |
| **Mac native** | ✅ | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ | ✅ | ✅ |
| **24/7 without PC** | ✅ | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ | ✅ | ✅ |
| **Free trial** | 7 days | 7 days | 14 days | ✅ | 7 days | Limited | ✅ | ✅ | ✅ |

---

## 2. Broker & Platform Support

| Platform / Integration | Relay (MVP→Roadmap) | Tradesyncer | Thor | Lune | Copilink | Replikanto | Trada |
|--------------------------|---------------------|-------------|------|------|----------|------------|-------|
| **Tradovate API** | ✅ MVP | ✅ | ✅ | ✅ | ✅ | ⚠️ | ✅ |
| **Rithmic** | 🔜 Phase 2 | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| **NinjaTrader 8** | 🔜 Phase 2 | ✅ | ✅ | ✅ | ✅ (host) | ✅ (host) | ✅ |
| **TradingView webhooks** | 🔜 Phase 2 | ✅ | ✅ | ⚠️ | ⚠️ | ⚠️ | ✅ |
| **ProjectX / TopstepX** | 🔜 Phase 3 | ✅ | ✅ | ⚠️ | ❌ | ❌ | ⚠️ |
| **DxFeed / Volumetrica** | 🔜 Phase 3 | ✅ | ✅ | ⚠️ | ❌ | ❌ | ✅ |
| **MT4 / MT5** | ❌ | ❌ | ✅ | ❌ | ❌ | ❌ | ✅ |
| **cTrader / DXtrade** | ❌ | ❌ | ✅ | ❌ | ❌ | ❌ | ✅ |
| **TradeLocker / MatchTrader** | ❌ | ❌ | ⚠️ | ❌ | ❌ | ❌ | ✅ |
| **Cross-broker copy** | ✅ (Tradovate MVP) | ✅ | ✅ | ✅ | ✅ | ⚠️ | ✅ |

---

## 3. Trade Copy Engine

| Feature | Relay | Tradesyncer | Thor | Lune | Copilink | Replikanto | Tradecopia | MimikTrader |
|---------|-------|-------------|------|------|----------|------------|------------|-------------|
| **Leader → Follower model** | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| **Market orders** | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| **Limit orders** | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| **Stop orders** | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| **Bracket orders (SL+TP)** | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ⚠️ | ✅ |
| **OCO orders** | 🔜 Phase 2 | ✅ | ✅ | ⚠️ | ✅ | ✅ | ⚠️ | ✅ |
| **Order modify/cancel sync** | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ⚠️ | ✅ |
| **Market-only follower mode** | ✅ | ✅ | ✅ | ✅ | ✅ | ⚠️ | ⚠️ | ⚠️ |
| **Multiple copy groups** | 🔜 Phase 2 | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| **Claimed latency** | <50ms P95 target | <100ms | 17ms | 5–10ms | ~1.6ms | 5–15ms | ~1.6ms | — |
| **Position reconciliation** | ✅ | ⚠️ | ✅ | ✅ | ✅ | ✅ (Guard) | ⚠️ | ✅ |

---

## 4. Position Sizing & Instrument Mapping

| Feature | Relay | Tradesyncer | Thor | Lune | Copilink | Replikanto | Trada |
|---------|-------|-------------|------|------|----------|------------|-------|
| **Fixed contract sizing** | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| **Ratio / multiplier sizing** | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| **Balance-proportional sizing** | ✅ | ✅ | ✅ | ✅ | ✅ | ⚠️ | ✅ |
| **Per-follower custom sizing** | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| **ES↔MES / NQ↔MNQ mapping** | 🔜 Phase 2 | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| **Skip follower below min size** | ✅ | ✅ | ✅ | ✅ | ✅ | ⚠️ | ✅ |
| **Symbol filter per account** | 🔜 Phase 2 | ⚠️ | ✅ | ⚠️ | ✅ | ⚠️ | ✅ |

---

## 5. Risk Management & Prop Firm Compliance

| Feature | Relay | Tradesyncer | Thor | Lune | Copilink | Replikanto | Trada | MimikTrader |
|---------|-------|-------------|------|------|----------|------------|-------|-------------|
| **Per-account daily loss limit** | ✅ MVP | ✅ | ✅ | ✅ | ✅ | ⚠️ | ✅ | ✅ (Pro) |
| **Auto-flatten on breach** | ✅ MVP | ✅ | ✅ | ✅ | ✅ | ❌ | ✅ | ✅ (Pro) |
| **Account lock after breach** | ✅ MVP | ✅ | ✅ | ✅ | ✅ | ⚠️ | ✅ | ✅ |
| **Per-account (not global) actions** | ✅ | ✅ | ✅ | ✅ | ✅ | ⚠️ | ✅ | ✅ |
| **Max contracts per account** | ✅ MVP | ✅ | ✅ | ✅ | ✅ | ⚠️ | ✅ | ✅ |
| **Daily profit target / pause** | 🔜 Phase 2 | ⚠️ | ✅ | ✅ | ✅ | ❌ | ✅ | ✅ |
| **Trailing drawdown tracking** | 🔜 Phase 2 | ⚠️ | ✅ | ✅ | ✅ | ❌ | ✅ | ✅ (Pro) |
| **Consistency rule % monitor** | 🔜 Phase 2 | ❌ | ❌ | ❌ | ✅ | ❌ | ⚠️ | ⚠️ |
| **Pre-trade compliance block** | 🔜 Phase 2 | ❌ | ⚠️ | ❌ | ⚠️ | ❌ | ✅ | ⚠️ |
| **Session / time lockouts** | 🔜 Phase 2 | ✅ | ✅ | ✅ | ✅ | ⚠️ | ✅ | ✅ |
| **News blackout periods** | 🔜 Phase 3 | ❌ | ✅ (calendar) | ✅ | ❌ | ❌ | ⚠️ | ❌ |
| **Prop firm rule profiles** | 🔜 Phase 2 | ⚠️ | ⚠️ | ⚠️ | ✅ | ⚠️ | ✅ | ✅ |
| **Slippage buffer config** | ✅ | ⚠️ | ⚠️ | ⚠️ | ✅ | ❌ | ✅ | ⚠️ |
| **Per-tick risk enforcement** | 🔜 Phase 2 | ❌ | ⚠️ | ⚠️ | ✅ | ❌ | ⚠️ | ✅ |

---

## 6. Monitoring, Journal & Analytics

| Feature | Relay | Tradesyncer | Thor | Lune | Copilink | Replikanto | Thor Saga |
|---------|-------|-------------|------|------|----------|------------|-----------|
| **Real-time copy status** | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| **Fill-level audit log** | ✅ **Differentiator** | ⚠️ | ✅ | ⚠️ | ⚠️ | ⚠️ | ✅ |
| **Latency per copy event** | ✅ | ⚠️ | ✅ | ⚠️ | ❌ | ❌ | ✅ |
| **Unified trade journal** | 🔜 Phase 2 | ✅ | ✅ (bundled) | ⚠️ | ❌ | ❌ | ✅ |
| **P&L dashboard per account** | ✅ | ✅ | ✅ | ✅ | ✅ | ⚠️ | ✅ |
| **Performance analytics** | 🔜 Phase 2 | ✅ | ✅ | ⚠️ | ❌ | ❌ | ✅ |
| **Economic calendar** | 🔜 Phase 3 | ✅ | ✅ | ⚠️ | ❌ | ❌ | — |
| **AI trade insights** | 🔜 Phase 3 | ❌ | ✅ (Saga) | ❌ | ❌ | ❌ | ✅ |
| **Export CSV/JSON** | 🔜 Phase 2 | ⚠️ | ✅ | ⚠️ | ⚠️ | ❌ | ✅ |

---

## 7. Alerts & Integrations

| Feature | Relay | Tradesyncer | Thor | Copilink | Trada | MimikTrader |
|---------|-------|-------------|------|----------|-------|-------------|
| **Email alerts** | ✅ MVP | ✅ | ✅ | ⚠️ | ✅ | ✅ |
| **Push notifications** | 🔜 Phase 2 | ✅ | ⚠️ | ❌ | ✅ | ⚠️ |
| **Discord / Slack webhooks** | 🔜 Phase 2 | ⚠️ | ⚠️ | ❌ | ⚠️ | ❌ |
| **REST API** | 🔜 Phase 2 | ❌ | ✅ | ❌ | ⚠️ | ❌ |
| **Outbound event webhooks** | 🔜 Phase 2 | ❌ | ✅ | ❌ | ⚠️ | ❌ |
| **TradingView as signal source** | 🔜 Phase 2 | ✅ | ✅ | ⚠️ | ⚠️ | ✅ |

---

## 8. Pricing & Scale Economics

| Platform | Starting Price | Model | Connections | Accounts | Notes |
|----------|---------------|-------|-------------|----------|-------|
| **Relay (proposed)** | $39/mo | Flat tier | Unlimited | 10 (Starter) → Unlimited (Scale) | Undercut tiered models |
| **Tradesyncer** | $49/mo | Tiered | 2 → ∞ | 20 → 120+ | Features same all tiers |
| **Thor** | $39/mo | Flat | Unlimited | Unlimited | Best scale economics |
| **Lune** | ~$39/mo | Tiered | 2+ | 10+ | Cloud price leader |
| **Copilink** | Subscription | Tier | — | Unlimited | + NT8 license + VPS |
| **Replikanto** | $149–299 | Lifetime | — | 20+ perf-limited | + VPS $60–200/mo |
| **Tradecopia** | ~$40/mo | Tiered | — | Unlimited (Pro) | + VPS; weak Rithmic |
| **MimikTrader** | Tiered | Tier | — | Varies | Risk suite on Pro+ |
| **Tradovate Group Trade** | Free | Native | — | Same broker only | No cross-firm |

### Cost at Scale Example: 1 leader + 30 followers

| Platform | Est. Monthly Cost | Hidden Costs |
|----------|-------------------|--------------|
| Relay Scale (proposed) | $129 | None |
| Tradesyncer Pro/Flex | $99–149 | None |
| Thor | $39 | None |
| Copilink + VPS | ~$80–150+ | NT8 license, VPS |
| Replikanto + VPS | ~$60–200+ | NT8 license, one-time $299 |

---

## 9. Relay vs. Market — Gap Analysis

| Capability | Market Leader | Relay MVP | Relay Phase 2 | Priority to Close Gap |
|------------|---------------|-----------|---------------|----------------------|
| Platform breadth | Thor (11+) | Tradovate only | +Rithmic, TV, NT | High (Phase 2) |
| Latency | Copilink 1.6ms | Cloud ~30–80ms | Optional local bridge | Medium |
| Prop compliance depth | Copilink | Basic caps + daily loss | Full rule engine | **High** |
| Flat unlimited pricing | Thor $39 | $39 Starter (10 acct) | $129 unlimited | Medium |
| Built-in journal | Tradesyncer | Basic log only | Full analytics | Medium |
| API access | Thor | None | REST + webhooks | Medium |
| Pre-trade blocking | Trada | None | Rule engine | **High** |
| Fill audit transparency | None strong | **Core differentiator** | Enhanced | **Ship MVP** |

---

## 10. Feature Priority Matrix (Relay Build)

Impact vs. Effort for Relay roadmap:

```
HIGH IMPACT
    │
    │  [Daily loss + flatten]     [Prop rule profiles]
    │  [Bracket copy]             [Rithmic adapter]
    │  [Fill audit log]           [Pre-trade block]
    │  [Tradovate connect]
    │
    │  [TradingView webhooks]     [AI journal]
    │  [Cross-contract map]       [Economic calendar]
    │
LOW │  [Multi copy groups]        [MT4/MT5 support]
IMPACT
    └──────────────────────────────────────────────
         LOW EFFORT                    HIGH EFFORT
```

---

## 11. Summary Scorecard (Qualitative)

Ratings: ★★★★★ = best in class · ★ = weak · — = not applicable

| Dimension | Tradesyncer | Thor | Copilink | Relay Target |
|-----------|-------------|------|----------|--------------|
| Cloud convenience | ★★★★★ | ★★★★ | ★ | ★★★★★ |
| Execution latency | ★★★ | ★★★★ | ★★★★★ | ★★★ (★★★★ w/ bridge) |
| Prop firm compliance | ★★★ | ★★★ | ★★★★★ | ★★★★★ |
| Platform breadth | ★★★★ | ★★★★★ | ★★ | ★★ → ★★★★ |
| Pricing at scale | ★★★ | ★★★★★ | ★★★ | ★★★★ |
| Journal / analytics | ★★★★ | ★★★★ | ★★ | ★★ → ★★★★ |
| API / extensibility | ★★ | ★★★★★ | ★ | ★★ → ★★★★ |
| Execution transparency | ★★★ | ★★★ | ★★ | ★★★★★ |
| Brand / trust | ★★★★★ | ★★★ | ★★★ | ★ (new entrant) |

---

## Related Documents
- [PRD.md](./PRD.md)
- [COMPETITOR_ANALYSIS.md](./COMPETITOR_ANALYSIS.md)
- [MVP_DEFINITION.md](./MVP_DEFINITION.md)
