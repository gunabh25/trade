# Risk Engine Architecture

TradeFlow's risk engine protects follower accounts with user-configurable rules, real-time monitoring, automated breach responses, and a kill switch.

## System Overview

```mermaid
flowchart TB
    subgraph PreTrade["Pre-Trade Gate"]
        COPY["Copy Orchestrator"]
        EVAL["RiskEvaluator"]
    end

    subgraph Rules["Rule Evaluators"]
        KS["Kill Switch"]
        DL["Daily Loss"]
        DD["Max Drawdown"]
        PS["Max Position Size"]
        MC["Max Contracts"]
        TH["Trading Hours"]
        AS["Allowed Symbols"]
        BS["Blocked Symbols"]
        LV["Leverage Limit"]
    end

    subgraph State["Real-Time State"]
        REDIS["Redis State Store"]
        SNAP["Monitor Snapshots"]
    end

    subgraph Actions["Automated Actions"]
        FLAT["Auto Flatten"]
        STOP["Auto Stop Copying"]
        LOCK["Lock Account"]
        ALERT["Alert System"]
    end

    subgraph Background["Background Jobs"]
        CELERY["Celery Beat 30s"]
        MON["RiskMonitor"]
    end

    COPY --> EVAL
    EVAL --> Rules
    EVAL --> REDIS
    MON --> EVAL
    MON --> Actions
    CELERY --> MON
    Actions --> ALERT
    MON --> SNAP
```

## Rule Evaluation Flow

```mermaid
sequenceDiagram
    participant C as Copy Engine
    participant E as RiskEvaluator
    participant R as Rule Chain
    participant S as Redis State
    participant A as ActionExecutor
    participant N as AlertService

    C->>E: check_pre_trade(rule, order)
    E->>S: get_state(account)
    E->>R: evaluate all rules
    alt violation
        R-->>E: RiskViolation[]
        E-->>C: allowed=false
        Note over C: Order blocked
    else pass
        E-->>C: allowed=true
        C->>C: execute copy
    end

    Note over E,A: Background monitor (every 30s)
    E->>R: check_account (no order)
    R-->>E: violation
    E->>A: handle_breach
    A->>A: flatten / stop copying / lock
    A->>N: send notification
```

## Configurable Rules

| Rule                  | Field                         | Action on Breach    |
| --------------------- | ----------------------------- | ------------------- |
| **Daily Loss**        | `daily_loss_limit_usd`        | Stop copying        |
| **Max Drawdown**      | `trailing_drawdown_limit_usd` | Flatten positions   |
| **Max Position Size** | `max_position_size_usd`       | Block order         |
| **Max Contracts**     | `max_total_contracts`         | Block order         |
| **Max Per Symbol**    | `max_contracts_per_symbol`    | Block order         |
| **Trading Hours**     | `start/end/timezone`          | Block order         |
| **Allowed Symbols**   | `allowed_symbols[]`           | Block order         |
| **Blocked Symbols**   | `blocked_symbols[]`           | Block order         |
| **Leverage Limit**    | `max_leverage`                | Block order         |
| **Kill Switch**       | `kill_switch_active`          | Block all + flatten |

All rules are individually enable/disable via `enabled` flag. Automated responses configurable via `auto_flatten_on_breach` and `auto_stop_copying_on_breach`.

## Kill Switch State Machine

```mermaid
stateDiagram-v2
    [*] --> Active: account trading normally
    Active --> KillSwitch: user activates / breach
    KillSwitch --> KillSwitch: all orders blocked
    KillSwitch --> Active: user deactivates
    KillSwitch --> Flattened: auto_flatten_on_breach
    Flattened --> StoppedCopy: auto_stop_copying_on_breach
```

## Database Schema

```mermaid
erDiagram
    users ||--o{ risk_rules : configures
    risk_rules ||--|| trading_accounts : protects
    risk_rules ||--o{ risk_breaches : generates
    trading_accounts ||--o{ risk_monitor_snapshots : tracked

    risk_rules {
        uuid id PK
        string name
        boolean enabled
        decimal daily_loss_limit_usd
        decimal trailing_drawdown_limit_usd
        decimal max_position_size_usd
        int max_contracts_per_symbol
        int max_total_contracts
        decimal max_leverage
        jsonb allowed_symbols
        jsonb blocked_symbols
        time trading_hours_start
        time trading_hours_end
        boolean kill_switch_active
        boolean auto_flatten_on_breach
        boolean auto_stop_copying_on_breach
    }

    risk_breaches {
        uuid id PK
        enum breach_type
        enum action_taken
        text message
        decimal current_value
        decimal limit_value
    }

    risk_monitor_snapshots {
        uuid id PK
        enum status
        decimal daily_pnl
        decimal drawdown_usd
        decimal current_leverage
    }
```

## Redis Keys

| Key                       | Purpose                                      |
| ------------------------- | -------------------------------------------- |
| `risk:state:{account_id}` | Real-time P&L, drawdown, contracts, leverage |
| `risk:status:{user_id}`   | Pub/sub for live UI updates                  |

## API Endpoints

| Method | Path                                             | Description          |
| ------ | ------------------------------------------------ | -------------------- |
| POST   | `/api/v1/risk/rules`                             | Create risk rule     |
| GET    | `/api/v1/risk/rules`                             | List all rules       |
| PUT    | `/api/v1/risk/rules/{id}`                        | Update configuration |
| DELETE | `/api/v1/risk/rules/{id}`                        | Delete rule          |
| POST   | `/api/v1/risk/rules/{id}/kill-switch/activate`   | Kill switch ON       |
| POST   | `/api/v1/risk/rules/{id}/kill-switch/deactivate` | Kill switch OFF      |
| POST   | `/api/v1/risk/accounts/{id}/flatten`             | Manual flatten       |
| GET    | `/api/v1/risk/accounts/{id}/status`              | Live monitor status  |
| GET    | `/api/v1/risk/breaches`                          | Breach history       |
| POST   | `/api/v1/risk/accounts/{id}/check`               | Pre-trade check      |

## Celery Background Jobs

| Task                   | Schedule  | Queue  |
| ---------------------- | --------- | ------ |
| `monitor_all_accounts` | Every 30s | `risk` |
| `reset_daily_sessions` | Every 1h  | `risk` |

## Module Layout

```
apps/api/src/tradeflow/risk/
├── types.py       # ProposedOrder, AccountRiskState, RiskCheckResult
├── state.py       # Redis state store
├── rules.py       # Individual rule evaluators (Strategy pattern)
├── evaluator.py   # Orchestrates all rules
├── actions.py     # Flatten, stop copying, kill switch
├── alerts.py      # Notifications + pub/sub
└── monitor.py     # Background account monitoring

apps/api/src/tradeflow/features/risk/
├── router.py      # REST API
├── service.py     # Business logic
└── schemas.py     # Pydantic models
```

## Integration with Copy Engine

The copy orchestrator calls `RiskEvaluator.check_pre_trade()` before every follower order placement. Blocked orders are logged in copy events with `risk_blocked` reason. Background monitor catches breaches from P&L/drawdown changes between trades.
