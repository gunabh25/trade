# TradeFlow AI — PostgreSQL Database Design

Normalized relational schema for the TradeFlow AI multi-account trade copier platform. All models live in `apps/api/src/tradeflow/db/models/` with Alembic migrations in `apps/api/alembic/versions/`.

---

## Design Principles

| Principle                   | Implementation                                                                                                                |
| --------------------------- | ----------------------------------------------------------------------------------------------------------------------------- |
| **UUID primary keys**       | Every table uses `UUID` (`gen_random_uuid()` via app default) for distributed-safe identifiers                                |
| **Third normal form (3NF)** | Roles, plans, broker credentials, and trading accounts are separate entities — no repeating groups or transitive dependencies |
| **Soft delete**             | `deleted_at TIMESTAMPTZ NULL` on mutable domain tables; partial unique indexes enforce uniqueness only among active rows      |
| **Timestamps**              | `created_at` + `updated_at` on all mutable tables; `audit_logs` and `billing_events` are append-only                          |
| **Referential integrity**   | Foreign keys with explicit `ON DELETE` rules (CASCADE, RESTRICT, SET NULL)                                                    |
| **Query-oriented indexes**  | Composite indexes aligned to dashboard queries (user + date, account + status, etc.)                                          |

---

## Entity-Relationship Diagram

```mermaid
erDiagram
    users ||--o{ user_roles : has
    roles ||--o{ user_roles : assigned
    users ||--o{ sessions : authenticates
    users ||--o{ oauth_accounts : links
    users ||--o{ api_keys : owns
    users ||--o{ broker_connections : connects
    users ||--o{ trading_accounts : owns
    users ||--o{ strategies : defines
    users ||--o{ orders : places
    users ||--o{ trades : executes
    users ||--o{ trade_journals : writes
    users ||--o{ notes : attaches
    users ||--o{ risk_rules : configures
    users ||--o{ notifications : receives
    users ||--o{ subscriptions : subscribes
    users ||--o{ billing_events : billed
    users ||--o{ audit_logs : audited

    plans ||--o{ subscriptions : tier
    subscriptions ||--o{ billing_events : generates

    broker_connections ||--o{ trading_accounts : feeds
    trading_accounts ||--|| risk_rules : enforces
    trading_accounts ||--o{ orders : receives
    trading_accounts ||--o{ trades : records
    trading_accounts ||--o{ positions : holds
    trading_accounts ||--o{ trade_journals : scopes

    strategies ||--o{ orders : tags
    strategies ||--o{ trades : tags
    orders ||--o{ orders : copies
    orders ||--o{ trades : fills
    trades ||--o{ trade_journals : reviews

    users {
        uuid id PK
        varchar email
        varchar password_hash
        timestamptz deleted_at
    }

    roles {
        uuid id PK
        varchar name UK
    }

    sessions {
        uuid id PK
        uuid user_id FK
        varchar token_hash UK
        timestamptz expires_at
    }

    oauth_accounts {
        uuid id PK
        uuid user_id FK
        varchar provider
        varchar provider_account_id
    }

    broker_connections {
        uuid id PK
        uuid user_id FK
        varchar broker
        text credentials_encrypted
    }

    trading_accounts {
        uuid id PK
        uuid user_id FK
        uuid broker_connection_id FK
        varchar external_account_id
        varchar account_role
    }

    orders {
        uuid id PK
        uuid trading_account_id FK
        uuid parent_order_id FK
        varchar symbol
        varchar status
    }

    trades {
        uuid id PK
        uuid trading_account_id FK
        uuid order_id FK
        varchar symbol
        numeric realized_pnl
    }

    positions {
        uuid id PK
        uuid trading_account_id FK
        varchar symbol
        int quantity
    }

    risk_rules {
        uuid id PK
        uuid trading_account_id FK UK
        numeric daily_loss_limit_usd
    }

    plans {
        uuid id PK
        varchar code UK
        int price_cents
    }

    subscriptions {
        uuid id PK
        uuid user_id FK
        uuid plan_id FK
        varchar status
    }

    billing_events {
        uuid id PK
        uuid user_id FK
        uuid subscription_id FK
        varchar event_type
    }

    audit_logs {
        uuid id PK
        uuid user_id FK
        varchar action
        jsonb old_values
    }

    api_keys {
        uuid id PK
        uuid user_id FK
        varchar key_prefix
        varchar key_hash
    }
```

---

## Table Catalog — Why Each Table Exists

### Identity & Access

#### `users`

**Why:** Root identity entity. Every piece of user-owned data hangs off `users.id`. Separating profile/auth fields from roles, sessions, and OAuth avoids repeating permission data and supports multiple auth methods (password + OAuth) on one account.

| Column                            | Purpose                                                       |
| --------------------------------- | ------------------------------------------------------------- |
| `email`                           | Login identifier; unique among active users via partial index |
| `password_hash`                   | Nullable — OAuth-only users have no local password            |
| `stripe_customer_id`              | Links to Stripe billing without duplicating payment data      |
| `is_active` / `email_verified_at` | Account lifecycle flags                                       |
| `deleted_at`                      | Soft delete preserves audit trail and billing history         |

#### `roles`

**Why:** Named permission bundles (`admin`, `trader`, `support`) stored once and referenced via junction table. Avoids embedding role strings on `users` (violates 3NF when users hold multiple roles).

#### `user_roles`

**Why:** Many-to-many junction between `users` and `roles`. A trader can also be an admin; permissions are resolved at query time from role assignments.

#### `sessions`

**Why:** Server-side session store for web dashboard auth. Stores hashed tokens (never plaintext), expiry, and revocation. Separate from `users` because one user holds many concurrent sessions across devices.

#### `oauth_accounts`

**Why:** Third-party identity linkage (Google, Apple, Microsoft) is orthogonal to local credentials. One user can link multiple providers. Tokens are encrypted at rest. Unique on `(provider, provider_account_id)` prevents duplicate OAuth bindings.

#### `api_keys`

**Why:** Programmatic API access separate from browser sessions. Stores only `key_prefix` (for lookup) and `key_hash` (never the raw key). Supports scoped permissions, expiry, and revocation independent of user password changes.

---

### Broker & Trading

#### `broker_connections`

**Why:** Encrypted broker API credentials (Tradovate, Rithmic, etc.) are a **connection** — not an individual trading account. One login can expose many sub-accounts. Separating credentials from accounts allows reconnecting without re-importing account metadata and enforces plan limits on connections vs accounts independently.

#### `trading_accounts`

**Why:** Individual broker sub-account used as leader or follower in the copy engine. References `broker_connection_id` for credentials and carries account-specific metadata (role, type, balance). Unique on `(broker_connection_id, external_account_id)` among active rows prevents duplicate imports.

#### `orders`

**Why:** Order intent and lifecycle — submitted, partial, filled, canceled. `parent_order_id` self-reference links leader orders to follower copies for fill-level audit. `strategy_id` tags orders for analytics without denormalizing strategy name.

#### `trades`

**Why:** Executed trade lifecycle from entry through exit with realized P&L. Distinct from `orders` because one order can produce multiple fills/trades and trades persist after orders complete. Supports journal and analytics queries by `opened_at` and `status`.

#### `positions`

**Why:** Current open position snapshot per account + symbol. Denormalized for fast dashboard reads; updated by the copy engine on fill events. One active position per `(trading_account_id, symbol)` enforced by partial unique index.

---

### Journal & Strategy

#### `strategies`

**Why:** User-defined strategy metadata (name, symbols, config JSON). Referenced optionally by orders and trades for tagging — avoids embedding strategy config on every trade row.

#### `trade_journals`

**Why:** Structured session reviews (title, mood, P&L, tags) separate from free-form notes. Optional links to `trading_account_id` and `trade_id` for context without requiring both.

#### `notes`

**Why:** Polymorphic free-form annotations via `(entity_type, entity_id)`. One table serves notes on trades, journals, strategies, accounts, and orders — avoids five nearly identical note tables (DRY, normalized entity reference).

---

### Risk

#### `risk_rules`

**Why:** Per-account risk thresholds (daily loss limit, max contracts, trailing drawdown). One-to-one with `trading_accounts` via unique constraint — each account has exactly one active rule set. `config` JSONB holds broker-specific extensions without schema migrations.

---

### Notifications

#### `notifications`

**Why:** In-app alert inbox for copy failures, connection loss, risk breaches, billing events. Separate from audit logs — notifications are user-facing and dismissible; audit logs are compliance-grade and immutable.

---

### Billing

#### `plans`

**Why:** Subscription tier catalog (Starter $39/mo, Pro, Scale) with feature limits (`max_trading_accounts`, `max_broker_connections`). Referenced by subscriptions — price changes don't mutate historical billing records.

#### `subscriptions`

**Why:** Active billing relationship between user and plan. Tracks Stripe subscription ID, trial/period dates, and status. `ON DELETE RESTRICT` on `plan_id` prevents deleting plans with active subscribers.

#### `billing_events`

**Why:** Immutable payment lifecycle events (invoice paid/failed, subscription created/canceled, refunds). Append-only — no soft delete. `stripe_event_id` unique constraint provides idempotent webhook processing.

---

### Compliance

#### `audit_logs`

**Why:** Tamper-evident append-only audit trail for security and compliance. Records who did what, when, from where, with before/after JSON snapshots. **No soft delete, no `updated_at`** — rows are never modified after insert. `user_id` SET NULL on user delete preserves the log entry.

---

## Foreign Key Cascade Matrix

| Child Table          | FK Column              | Parent               | ON DELETE    | Rationale                                     |
| -------------------- | ---------------------- | -------------------- | ------------ | --------------------------------------------- |
| `user_roles`         | `user_id`              | `users`              | CASCADE      | Role assignments are owned by user            |
| `user_roles`         | `role_id`              | `roles`              | CASCADE      | Remove assignments when role deleted          |
| `sessions`           | `user_id`              | `users`              | CASCADE      | Sessions die with user                        |
| `oauth_accounts`     | `user_id`              | `users`              | CASCADE      | OAuth links owned by user                     |
| `api_keys`           | `user_id`              | `users`              | CASCADE      | Keys owned by user                            |
| `broker_connections` | `user_id`              | `users`              | CASCADE      | Connections owned by user                     |
| `trading_accounts`   | `user_id`              | `users`              | CASCADE      | Accounts owned by user                        |
| `trading_accounts`   | `broker_connection_id` | `broker_connections` | **RESTRICT** | Cannot delete connection with active accounts |
| `orders`             | `user_id`              | `users`              | CASCADE      | Orders owned by user                          |
| `orders`             | `trading_account_id`   | `trading_accounts`   | CASCADE      | Orders scoped to account                      |
| `orders`             | `strategy_id`          | `strategies`         | SET NULL     | Preserve order if strategy deleted            |
| `orders`             | `parent_order_id`      | `orders`             | SET NULL     | Preserve child if parent deleted              |
| `trades`             | `user_id`              | `users`              | CASCADE      | Trades owned by user                          |
| `trades`             | `trading_account_id`   | `trading_accounts`   | CASCADE      | Trades scoped to account                      |
| `trades`             | `order_id`             | `orders`             | SET NULL     | Preserve trade if order purged                |
| `trades`             | `strategy_id`          | `strategies`         | SET NULL     | Preserve trade if strategy deleted            |
| `positions`          | `trading_account_id`   | `trading_accounts`   | CASCADE      | Positions scoped to account                   |
| `risk_rules`         | `user_id`              | `users`              | CASCADE      | Rules owned by user                           |
| `risk_rules`         | `trading_account_id`   | `trading_accounts`   | CASCADE      | Rules scoped to account                       |
| `trade_journals`     | `user_id`              | `users`              | CASCADE      | Journals owned by user                        |
| `trade_journals`     | `trading_account_id`   | `trading_accounts`   | SET NULL     | Keep journal if account removed               |
| `trade_journals`     | `trade_id`             | `trades`             | SET NULL     | Keep journal if trade purged                  |
| `notes`              | `user_id`              | `users`              | CASCADE      | Notes owned by user                           |
| `notifications`      | `user_id`              | `users`              | CASCADE      | Notifications owned by user                   |
| `subscriptions`      | `user_id`              | `users`              | CASCADE      | Subscriptions owned by user                   |
| `subscriptions`      | `plan_id`              | `plans`              | **RESTRICT** | Cannot delete plan with subscribers           |
| `billing_events`     | `user_id`              | `users`              | CASCADE      | Events owned by user                          |
| `billing_events`     | `subscription_id`      | `subscriptions`      | SET NULL     | Preserve event if subscription removed        |
| `audit_logs`         | `user_id`              | `users`              | SET NULL     | Preserve audit entry after user deletion      |

---

## Index Catalog

### Partial Unique Indexes (soft-delete aware)

| Index                                 | Columns                                     | Condition            | Purpose                      |
| ------------------------------------- | ------------------------------------------- | -------------------- | ---------------------------- |
| `uq_users_email_active`               | `email`                                     | `deleted_at IS NULL` | One active email per user    |
| `uq_trading_accounts_external_active` | `broker_connection_id, external_account_id` | `deleted_at IS NULL` | No duplicate account imports |
| `uq_positions_account_symbol_active`  | `trading_account_id, symbol`                | `deleted_at IS NULL` | One open position per symbol |

### Composite Indexes (query patterns)

| Index                                                 | Columns                                  | Query Pattern                   |
| ----------------------------------------------------- | ---------------------------------------- | ------------------------------- |
| `ix_trading_accounts_user_id_deleted_at`              | `user_id, deleted_at`                    | List user's active accounts     |
| `ix_trading_accounts_broker_connection_id_deleted_at` | `broker_connection_id, deleted_at`       | Accounts under a connection     |
| `ix_orders_trading_account_id_status_created_at`      | `trading_account_id, status, created_at` | Account order history by status |
| `ix_orders_user_id_created_at`                        | `user_id, created_at`                    | User-wide order timeline        |
| `ix_trades_trading_account_id_status_opened_at`       | `trading_account_id, status, opened_at`  | Account trade history           |
| `ix_trades_user_id_opened_at`                         | `user_id, opened_at`                     | User trade timeline             |
| `ix_positions_trading_account_id_deleted_at`          | `trading_account_id, deleted_at`         | Active positions for account    |
| `ix_notifications_user_id_read_at_created_at`         | `user_id, read_at, created_at`           | Unread notifications inbox      |
| `ix_trade_journals_user_id_session_date`              | `user_id, session_date`                  | Journal calendar view           |
| `ix_notes_user_id_entity`                             | `user_id, entity_type, entity_id`        | Notes for a specific entity     |
| `ix_audit_logs_user_id_created_at`                    | `user_id, created_at`                    | User activity audit             |
| `ix_audit_logs_resource`                              | `resource_type, resource_id`             | Audit for a specific resource   |
| `ix_audit_logs_action_created_at`                     | `action, created_at`                     | Filter by action type           |
| `ix_api_keys_user_id_deleted_at`                      | `user_id, deleted_at`                    | Active API keys for user        |
| `ix_api_keys_key_prefix`                              | `key_prefix`                             | Key lookup on auth              |
| `ix_strategies_user_id_deleted_at`                    | `user_id, deleted_at`                    | Active strategies               |
| `ix_risk_rules_user_id_deleted_at`                    | `user_id, deleted_at`                    | Active risk rules               |

---

## Soft Delete Policy

| Table                                   | Soft Delete | Reason                                   |
| --------------------------------------- | ----------- | ---------------------------------------- |
| `users`                                 | Yes         | Preserve billing/audit references        |
| `roles`                                 | No          | Reference data; use `user_roles` cascade |
| `sessions`                              | No          | Hard revoke via `revoked_at`             |
| `oauth_accounts`                        | No          | Hard delete on unlink                    |
| `broker_connections`                    | Yes         | Preserve historical trade data           |
| `trading_accounts`                      | Yes         | Preserve order/trade history             |
| `orders`, `trades`, `positions`         | Yes         | Compliance and analytics                 |
| `strategies`, `trade_journals`, `notes` | Yes         | User content recovery                    |
| `risk_rules`                            | Yes         | Historical rule audit                    |
| `notifications`                         | Yes         | User can dismiss/archive                 |
| `plans`                                 | Yes         | Retire tiers without breaking FK         |
| `subscriptions`                         | Yes         | Billing history preservation             |
| `billing_events`                        | **No**      | Immutable financial record               |
| `audit_logs`                            | **No**      | Tamper-evident compliance                |
| `api_keys`                              | Yes         | Revoke without losing audit trail        |

**Application convention:** All queries on soft-deletable tables MUST filter `WHERE deleted_at IS NULL` unless explicitly querying archived data.

---

## Migrations

| Revision                   | File                          | Description                                                        |
| -------------------------- | ----------------------------- | ------------------------------------------------------------------ |
| `001_initial_schema`       | `001_initial_schema.py`       | Creates all 20 tables, indexes, and partial unique indexes         |
| `002_seed_roles_and_plans` | `002_seed_roles_and_plans.py` | Seeds `admin`/`trader`/`support` roles and Starter/Pro/Scale plans |

### Run migrations

```bash
# Start Postgres
docker compose up -d postgres

# From apps/api with venv activated
cd apps/api
source .venv/bin/activate
export DATABASE_URL_SYNC=postgresql+psycopg://tradeflow:tradeflow_dev_password@localhost:5432/tradeflow
alembic upgrade head
```

### Generate new migration (after model changes)

```bash
alembic revision --autogenerate -m "describe_change"
```

---

## File Map

```
apps/api/src/tradeflow/db/
├── base.py              # DeclarativeBase
├── mixins.py            # TimestampMixin, SoftDeleteMixin
├── enums.py             # Domain string enums
├── session.py           # Async session factory
└── models/
    ├── __init__.py      # Model registry (Alembic import)
    ├── user.py          # users, roles, user_roles
    ├── session.py       # sessions
    ├── oauth.py         # oauth_accounts
    ├── api_key.py       # api_keys
    ├── broker.py        # broker_connections
    ├── trading.py       # trading_accounts, orders, trades, positions
    ├── journal.py       # strategies, trade_journals, notes
    ├── risk.py          # risk_rules
    ├── notification.py  # notifications
    ├── billing.py       # plans, subscriptions, billing_events
    └── audit.py         # audit_logs

apps/api/alembic/
├── env.py
└── versions/
    ├── 001_initial_schema.py
    └── 002_seed_roles_and_plans.py
```

---

## Normalization Summary

| Form     | How It's Satisfied                                                                                                                                                 |
| -------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| **1NF**  | Atomic columns; JSONB used only for extensible config/metadata, not core relational data                                                                           |
| **2NF**  | All non-key attributes depend on the full primary key (no composite PKs with partial dependencies)                                                                 |
| **3NF**  | Roles, plans, broker credentials, strategies separated from entities that reference them; no transitive dependencies (e.g., plan price is on `plans`, not `users`) |
| **BCNF** | Junction tables (`user_roles`) decompose many-to-many; `risk_rules` 1:1 with accounts via unique FK                                                                |
