# Copy Engine Architecture

TradeFlow's copy engine is the heart of the platform — it replicates leader trades to follower accounts with configurable sizing, ultra-low latency execution, and fault tolerance.

## System Overview

```mermaid
flowchart TB
    subgraph Leader["Leader Account"]
        LW["Broker WebSocket / REST"]
        LE["Leader Order Event"]
    end

    subgraph HotPath["Hot Path (API / Celery)"]
        ORCH["CopyOrchestrator"]
        DED["Redis Dedupe"]
        MATCH["OrderMatcher"]
        SIZE["Sizing Engine"]
        EXEC["CopyExecutor"]
    end

    subgraph Followers["Follower Accounts"]
        F1["Follower 1"]
        F2["Follower 2"]
        FN["Follower N"]
    end

    subgraph Infra["Infrastructure"]
        REDIS["Redis"]
        PG["PostgreSQL"]
        CELERY["Celery Workers"]
    end

    LW --> LE
    LE --> ORCH
    ORCH --> DED
    DED --> REDIS
    ORCH --> MATCH
    MATCH --> SIZE
    ORCH --> EXEC
    EXEC --> F1 & F2 & FN
    EXEC --> PG
    ORCH --> PG
    ORCH -.->|failed| RETRY["Retry Queue"]
    RETRY --> REDIS
    CELERY -->|drain| RETRY
    CELERY --> ORCH
```

## Data Flow — Leader Event to Follower Execution

```mermaid
sequenceDiagram
    participant L as Leader Broker
    participant O as CopyOrchestrator
    participant R as Redis
    participant M as OrderMatcher
    participant E as CopyExecutor
    participant F as Follower Broker
    participant DB as PostgreSQL

    L->>O: LeaderEvent (order_submitted)
    O->>R: SET dedupe:{event_id} NX
    alt duplicate
        R-->>O: null (skip)
    end
    O->>M: plan_copies(event, followers)
    M-->>O: CopyDecision[]

    par Parallel execution (semaphore)
        O->>E: execute(decision_1)
        E->>F: place_order()
        F-->>E: BrokerOrder
        E->>DB: Order + OrderMapping
    and
        O->>E: execute(decision_2)
        E->>F: place_order()
    end

    O->>DB: CopyEvent (audit)
    O->>R: PUBLISH copy:events:{user_id}
```

## Copy Modes

| Mode                      | Formula                    | Example                               |
| ------------------------- | -------------------------- | ------------------------------------- |
| **Fixed Quantity**        | `sizing_value`             | Leader buys 5 → Follower buys 3       |
| **Risk Multiplier**       | `leader_qty × multiplier`  | Leader buys 2, 2× → Follower buys 4   |
| **Percentage Allocation** | `leader_qty × (pct / 100)` | Leader buys 10, 50% → Follower buys 5 |
| **Reverse Copy**          | Same qty, flipped side     | Leader BUY 2 → Follower SELL 2        |

Partial fills scale proportionally: if leader fills 50% of a 10-lot order, the follower fills 50% of its calculated size.

## Order Types

Supported order types flow through the engine to broker adapters:

| Type            | Use Case                  |
| --------------- | ------------------------- |
| `market`        | Immediate execution       |
| `limit`         | Price-targeted entry/exit |
| `stop`          | Stop entry                |
| `stop_limit`    | Stop with limit price     |
| `stop_loss`     | Bracket stop leg          |
| `take_profit`   | Bracket target leg        |
| `trailing_stop` | Trailing stop leg         |

Bracket legs are tracked via `OrderMapping.leg_type` (`entry`, `stop`, `target`, `trailing`).

## Bracket Order State Machine

```mermaid
stateDiagram-v2
    [*] --> EntryPending: leader entry submitted
    EntryPending --> BracketActive: entry filled
    EntryPending --> Cancelled: entry cancelled
    BracketActive --> BracketActive: modify SL/TP
    BracketActive --> Closed: SL or TP filled
    BracketActive --> Flattened: risk breach
    Closed --> [*]
    Cancelled --> [*]
    Flattened --> [*]
```

## Retry & Failure Handling

```mermaid
flowchart LR
    EXEC["Execution Failed"]
    LOG["ExecutionLog"]
    RQ["Redis Retry Queue<br/>(sorted set)"]
    CELERY["Celery drain_retry_queue"]
    RETRY["Retry Execution"]
    DL["Dead Letter Queue"]

    EXEC --> LOG
    LOG --> RQ
    CELERY -->|every 5s| RQ
    RQ --> RETRY
    RETRY -->|success| DONE["Complete"]
    RETRY -->|max attempts| DL
```

- Exponential backoff: 1s, 2s, 4s, 8s, 16s
- Default max attempts: 5 (`COPY_RETRY_MAX_ATTEMPTS`)
- Dead-letter queue for manual investigation

## Connection Recovery

```mermaid
flowchart TB
    BEAT["Celery Beat (60s)"]
    REC["recover_connections task"]
    DB["Load active copy groups"]
    BC["Broker connections"]
    SM["BrokerSessionManager"]

    BEAT --> REC
    REC --> DB
    DB --> BC
    BC --> SM
    SM -->|reconnect| ADAPTERS["Broker Adapters"]
```

On disconnect, the broker adapter's auto-reconnect kicks in immediately. Celery beat provides a periodic safety net for sessions lost during API restarts.

## Module Layout

```
apps/api/src/tradeflow/
├── engine/
│   ├── types.py          # LeaderEvent, CopyDecision, FollowerContext
│   ├── sizing.py         # Copy mode calculations + partial fills
│   ├── order_types.py    # Order type normalization
│   ├── matching.py       # OrderMatcher — plan decisions
│   ├── mapping.py        # TradeMappingStore — Redis + DB
│   ├── executor.py       # CopyExecutor — broker I/O
│   ├── orchestrator.py   # CopyOrchestrator — hot path
│   ├── retry_queue.py    # Redis sorted-set retry queue
│   ├── sync.py           # Position/order reconciliation
│   └── recovery.py       # Connection recovery
├── features/copy_trading/
│   ├── router.py         # /api/v1/copy/*
│   ├── service.py        # Group CRUD + simulate
│   └── schemas.py        # Pydantic models
├── workers/
│   └── copy_tasks.py     # Celery tasks
└── db/models/
    └── copy_trading.py   # CopyGroup, CopyEvent, OrderMapping, ExecutionLog
```

## Database Schema

```mermaid
erDiagram
    users ||--o{ copy_groups : owns
    copy_groups ||--|| trading_accounts : leader
    copy_groups ||--o{ copy_group_followers : has
    copy_group_followers }o--|| trading_accounts : follower
    copy_groups ||--o{ copy_events : generates
    copy_groups ||--o{ order_mappings : tracks
    copy_groups ||--o{ execution_logs : retries
    orders ||--o{ order_mappings : links

    copy_groups {
        uuid id PK
        uuid leader_account_id FK
        string status
        boolean copying_enabled
    }

    copy_group_followers {
        uuid id PK
        enum copy_mode
        decimal sizing_value
        enum status
    }

    copy_events {
        uuid id PK
        string leader_event_id
        enum action
        enum result
        int latency_ms
    }

    order_mappings {
        uuid id PK
        string leader_order_id
        string follower_order_id
        enum leg_type
    }

    execution_logs {
        uuid id PK
        enum status
        int attempt
        jsonb payload
    }
```

## Redis Keys

| Key Pattern                                            | Purpose                                  | TTL |
| ------------------------------------------------------ | ---------------------------------------- | --- |
| `copy:dedupe:{event_id}`                               | Idempotency                              | 24h |
| `copy:mapping:{group}:{leader_order}:{follower}:{leg}` | Order mapping cache                      | 7d  |
| `copy:retry:queue`                                     | Retry sorted set (score = next_retry_at) | —   |
| `copy:retry:dead_letter`                               | Failed after max retries                 | —   |
| `copy:events:{user_id}`                                | Pub/sub for real-time UI                 | —   |

## API Endpoints

| Method | Path                                      | Description       |
| ------ | ----------------------------------------- | ----------------- |
| POST   | `/api/v1/copy/groups`                     | Create copy group |
| GET    | `/api/v1/copy/groups`                     | List groups       |
| POST   | `/api/v1/copy/groups/{id}/followers`      | Add follower      |
| POST   | `/api/v1/copy/groups/{id}/start`          | Start copying     |
| POST   | `/api/v1/copy/groups/{id}/stop`           | Stop copying      |
| GET    | `/api/v1/copy/groups/{id}/events`         | Audit log         |
| GET    | `/api/v1/copy/groups/{id}/execution-logs` | Retry logs        |
| POST   | `/api/v1/copy/groups/{id}/simulate`       | Inject test event |
| GET    | `/api/v1/copy/health`                     | Engine metrics    |

## Configuration

| Variable                             | Default | Description                      |
| ------------------------------------ | ------- | -------------------------------- |
| `COPY_RETRY_MAX_ATTEMPTS`            | 5       | Max retry attempts per execution |
| `COPY_MAX_PARALLEL_FOLLOWERS`        | 10      | Concurrent follower executions   |
| `COPY_HEALTH_CHECK_INTERVAL_SECONDS` | 15      | Health probe interval            |

## Latency Design

1. **Dedupe in Redis** — O(1) SET NX, no DB round-trip on duplicates
2. **Order mapping cache** — Redis first, DB fallback
3. **Parallel follower execution** — `asyncio.gather` with semaphore
4. **Async audit persist** — single flush after all followers complete
5. **Celery offload** — optional async path via `process_leader_event` task for non-blocking API

## Celery Tasks

| Task                   | Schedule  | Queue  |
| ---------------------- | --------- | ------ |
| `process_leader_event` | On demand | `copy` |
| `drain_retry_queue`    | Every 5s  | `copy` |
| `recover_connections`  | Every 60s | `copy` |
| `sync_copy_groups`     | On demand | `copy` |
