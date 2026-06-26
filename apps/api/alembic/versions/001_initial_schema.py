"""Initial normalized schema for TradeFlow AI."""

from collections.abc import Sequence

from alembic import op

revision: str = "001_initial_schema"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute("""
CREATE TABLE plans (
	id UUID NOT NULL,
	code VARCHAR(50) NOT NULL,
	name VARCHAR(100) NOT NULL,
	description TEXT,
	price_cents INTEGER NOT NULL,
	currency VARCHAR(3) NOT NULL,
	interval VARCHAR(20) NOT NULL,
	stripe_price_id VARCHAR(255),
	max_trading_accounts INTEGER NOT NULL,
	max_broker_connections INTEGER NOT NULL,
	is_active BOOLEAN NOT NULL,
	features JSONB,
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
	updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
	deleted_at TIMESTAMP WITH TIME ZONE,
	PRIMARY KEY (id),
	UNIQUE (code)
)
""")
    op.execute("""
CREATE TABLE roles (
	id UUID NOT NULL,
	name VARCHAR(50) NOT NULL,
	description TEXT,
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
	updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
	PRIMARY KEY (id),
	UNIQUE (name)
)
""")
    op.execute("""
CREATE TABLE users (
	id UUID NOT NULL,
	email VARCHAR(320) NOT NULL,
	password_hash VARCHAR(255),
	first_name VARCHAR(100),
	last_name VARCHAR(100),
	is_active BOOLEAN NOT NULL,
	email_verified_at TIMESTAMP WITH TIME ZONE,
	stripe_customer_id VARCHAR(255),
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
	updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
	deleted_at TIMESTAMP WITH TIME ZONE,
	PRIMARY KEY (id)
)
""")
    op.execute("""
CREATE TABLE api_keys (
	id UUID NOT NULL,
	user_id UUID NOT NULL,
	name VARCHAR(100) NOT NULL,
	key_prefix VARCHAR(16) NOT NULL,
	key_hash VARCHAR(128) NOT NULL,
	scopes JSONB,
	last_used_at TIMESTAMP WITH TIME ZONE,
	expires_at TIMESTAMP WITH TIME ZONE,
	revoked_at TIMESTAMP WITH TIME ZONE,
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
	updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
	deleted_at TIMESTAMP WITH TIME ZONE,
	PRIMARY KEY (id),
	FOREIGN KEY(user_id) REFERENCES users (id) ON DELETE CASCADE
)
""")
    op.execute("""
CREATE TABLE audit_logs (
	id UUID NOT NULL,
	user_id UUID,
	action VARCHAR(50) NOT NULL,
	resource_type VARCHAR(100) NOT NULL,
	resource_id UUID,
	ip_address INET,
	user_agent TEXT,
	old_values JSONB,
	new_values JSONB,
	metadata JSONB,
	created_at TIMESTAMP WITH TIME ZONE NOT NULL,
	PRIMARY KEY (id),
	FOREIGN KEY(user_id) REFERENCES users (id) ON DELETE SET NULL
)
""")
    op.execute("""
CREATE TABLE broker_connections (
	id UUID NOT NULL,
	user_id UUID NOT NULL,
	broker VARCHAR(50) NOT NULL,
	name VARCHAR(100) NOT NULL,
	status VARCHAR(30) NOT NULL,
	credentials_encrypted TEXT NOT NULL,
	external_user_id VARCHAR(255),
	token_expires_at TIMESTAMP WITH TIME ZONE,
	last_connected_at TIMESTAMP WITH TIME ZONE,
	last_error TEXT,
	metadata JSONB,
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
	updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
	deleted_at TIMESTAMP WITH TIME ZONE,
	PRIMARY KEY (id),
	FOREIGN KEY(user_id) REFERENCES users (id) ON DELETE CASCADE
)
""")
    op.execute("""
CREATE TABLE notes (
	id UUID NOT NULL,
	user_id UUID NOT NULL,
	entity_type VARCHAR(30) NOT NULL,
	entity_id UUID NOT NULL,
	title VARCHAR(200),
	content TEXT NOT NULL,
	is_pinned BOOLEAN NOT NULL,
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
	updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
	deleted_at TIMESTAMP WITH TIME ZONE,
	PRIMARY KEY (id),
	FOREIGN KEY(user_id) REFERENCES users (id) ON DELETE CASCADE
)
""")
    op.execute("""
CREATE TABLE notifications (
	id UUID NOT NULL,
	user_id UUID NOT NULL,
	type VARCHAR(50) NOT NULL,
	title VARCHAR(200) NOT NULL,
	body TEXT NOT NULL,
	read_at TIMESTAMP WITH TIME ZONE,
	action_url VARCHAR(500),
	metadata JSONB,
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
	updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
	deleted_at TIMESTAMP WITH TIME ZONE,
	PRIMARY KEY (id),
	FOREIGN KEY(user_id) REFERENCES users (id) ON DELETE CASCADE
)
""")
    op.execute("""
CREATE TABLE oauth_accounts (
	id UUID NOT NULL,
	user_id UUID NOT NULL,
	provider VARCHAR(50) NOT NULL,
	provider_account_id VARCHAR(255) NOT NULL,
	access_token_encrypted TEXT,
	refresh_token_encrypted TEXT,
	token_expires_at TIMESTAMP WITH TIME ZONE,
	scopes JSONB,
	profile_email VARCHAR(320),
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
	updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
	PRIMARY KEY (id),
	CONSTRAINT uq_oauth_accounts_provider_account UNIQUE (provider, provider_account_id),
	FOREIGN KEY(user_id) REFERENCES users (id) ON DELETE CASCADE
)
""")
    op.execute("""
CREATE TABLE sessions (
	id UUID NOT NULL,
	user_id UUID NOT NULL,
	token_hash VARCHAR(128) NOT NULL,
	ip_address VARCHAR(45),
	user_agent TEXT,
	expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
	revoked_at TIMESTAMP WITH TIME ZONE,
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
	updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
	PRIMARY KEY (id),
	FOREIGN KEY(user_id) REFERENCES users (id) ON DELETE CASCADE,
	UNIQUE (token_hash)
)
""")
    op.execute("""
CREATE TABLE strategies (
	id UUID NOT NULL,
	user_id UUID NOT NULL,
	name VARCHAR(100) NOT NULL,
	description TEXT,
	symbols JSONB,
	config JSONB,
	is_active BOOLEAN NOT NULL,
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
	updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
	deleted_at TIMESTAMP WITH TIME ZONE,
	PRIMARY KEY (id),
	FOREIGN KEY(user_id) REFERENCES users (id) ON DELETE CASCADE
)
""")
    op.execute("""
CREATE TABLE subscriptions (
	id UUID NOT NULL,
	user_id UUID NOT NULL,
	plan_id UUID NOT NULL,
	status VARCHAR(30) NOT NULL,
	stripe_subscription_id VARCHAR(255),
	trial_ends_at TIMESTAMP WITH TIME ZONE,
	current_period_start TIMESTAMP WITH TIME ZONE,
	current_period_end TIMESTAMP WITH TIME ZONE,
	canceled_at TIMESTAMP WITH TIME ZONE,
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
	updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
	deleted_at TIMESTAMP WITH TIME ZONE,
	PRIMARY KEY (id),
	FOREIGN KEY(user_id) REFERENCES users (id) ON DELETE CASCADE,
	FOREIGN KEY(plan_id) REFERENCES plans (id) ON DELETE RESTRICT
)
""")
    op.execute("""
CREATE TABLE user_roles (
	id UUID NOT NULL,
	user_id UUID NOT NULL,
	role_id UUID NOT NULL,
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
	updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
	PRIMARY KEY (id),
	CONSTRAINT uq_user_roles_user_id_role_id UNIQUE (user_id, role_id),
	FOREIGN KEY(user_id) REFERENCES users (id) ON DELETE CASCADE,
	FOREIGN KEY(role_id) REFERENCES roles (id) ON DELETE CASCADE
)
""")
    op.execute("""
CREATE TABLE billing_events (
	id UUID NOT NULL,
	user_id UUID NOT NULL,
	subscription_id UUID,
	event_type VARCHAR(50) NOT NULL,
	status VARCHAR(30) NOT NULL,
	amount_cents INTEGER,
	currency VARCHAR(3),
	stripe_invoice_id VARCHAR(255),
	stripe_event_id VARCHAR(255),
	metadata JSONB,
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
	updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
	PRIMARY KEY (id),
	FOREIGN KEY(user_id) REFERENCES users (id) ON DELETE CASCADE,
	FOREIGN KEY(subscription_id) REFERENCES subscriptions (id) ON DELETE SET NULL,
	UNIQUE (stripe_event_id)
)
""")
    op.execute("""
CREATE TABLE trading_accounts (
	id UUID NOT NULL,
	user_id UUID NOT NULL,
	broker_connection_id UUID NOT NULL,
	external_account_id VARCHAR(100) NOT NULL,
	name VARCHAR(100) NOT NULL,
	account_type VARCHAR(30) NOT NULL,
	account_role VARCHAR(30) NOT NULL,
	status VARCHAR(30) NOT NULL,
	currency VARCHAR(3) NOT NULL,
	balance NUMERIC(18, 2),
	metadata JSONB,
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
	updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
	deleted_at TIMESTAMP WITH TIME ZONE,
	PRIMARY KEY (id),
	FOREIGN KEY(user_id) REFERENCES users (id) ON DELETE CASCADE,
	FOREIGN KEY(broker_connection_id) REFERENCES broker_connections (id) ON DELETE RESTRICT
)
""")
    op.execute("""
CREATE TABLE orders (
	id UUID NOT NULL,
	user_id UUID NOT NULL,
	trading_account_id UUID NOT NULL,
	strategy_id UUID,
	parent_order_id UUID,
	external_order_id VARCHAR(100),
	symbol VARCHAR(50) NOT NULL,
	side VARCHAR(10) NOT NULL,
	order_type VARCHAR(20) NOT NULL,
	quantity INTEGER NOT NULL,
	filled_quantity INTEGER NOT NULL,
	price NUMERIC(18, 8),
	stop_price NUMERIC(18, 8),
	status VARCHAR(20) NOT NULL,
	submitted_at TIMESTAMP WITH TIME ZONE,
	filled_at TIMESTAMP WITH TIME ZONE,
	metadata JSONB,
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
	updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
	deleted_at TIMESTAMP WITH TIME ZONE,
	PRIMARY KEY (id),
	FOREIGN KEY(user_id) REFERENCES users (id) ON DELETE CASCADE,
	FOREIGN KEY(trading_account_id) REFERENCES trading_accounts (id) ON DELETE CASCADE,
	FOREIGN KEY(strategy_id) REFERENCES strategies (id) ON DELETE SET NULL,
	FOREIGN KEY(parent_order_id) REFERENCES orders (id) ON DELETE SET NULL
)
""")
    op.execute("""
CREATE TABLE positions (
	id UUID NOT NULL,
	trading_account_id UUID NOT NULL,
	symbol VARCHAR(50) NOT NULL,
	side VARCHAR(10) NOT NULL,
	quantity INTEGER NOT NULL,
	average_price NUMERIC(18, 8) NOT NULL,
	unrealized_pnl NUMERIC(18, 2),
	opened_at TIMESTAMP WITH TIME ZONE NOT NULL,
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
	updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
	deleted_at TIMESTAMP WITH TIME ZONE,
	PRIMARY KEY (id),
	FOREIGN KEY(trading_account_id) REFERENCES trading_accounts (id) ON DELETE CASCADE
)
""")
    op.execute("""
CREATE TABLE risk_rules (
	id UUID NOT NULL,
	user_id UUID NOT NULL,
	trading_account_id UUID NOT NULL,
	daily_loss_limit_usd NUMERIC(18, 2),
	max_contracts_per_symbol INTEGER,
	max_total_contracts INTEGER,
	trailing_drawdown_limit_usd NUMERIC(18, 2),
	session_reset_time TIME WITHOUT TIME ZONE,
	config JSONB,
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
	updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
	deleted_at TIMESTAMP WITH TIME ZONE,
	PRIMARY KEY (id),
	CONSTRAINT uq_risk_rules_trading_account_id UNIQUE (trading_account_id),
	FOREIGN KEY(user_id) REFERENCES users (id) ON DELETE CASCADE,
	FOREIGN KEY(trading_account_id) REFERENCES trading_accounts (id) ON DELETE CASCADE
)
""")
    op.execute("""
CREATE TABLE trades (
	id UUID NOT NULL,
	user_id UUID NOT NULL,
	trading_account_id UUID NOT NULL,
	order_id UUID,
	strategy_id UUID,
	symbol VARCHAR(50) NOT NULL,
	side VARCHAR(10) NOT NULL,
	quantity INTEGER NOT NULL,
	entry_price NUMERIC(18, 8) NOT NULL,
	exit_price NUMERIC(18, 8),
	realized_pnl NUMERIC(18, 2),
	fees NUMERIC(18, 4),
	status VARCHAR(20) NOT NULL,
	opened_at TIMESTAMP WITH TIME ZONE NOT NULL,
	closed_at TIMESTAMP WITH TIME ZONE,
	metadata JSONB,
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
	updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
	deleted_at TIMESTAMP WITH TIME ZONE,
	PRIMARY KEY (id),
	FOREIGN KEY(user_id) REFERENCES users (id) ON DELETE CASCADE,
	FOREIGN KEY(trading_account_id) REFERENCES trading_accounts (id) ON DELETE CASCADE,
	FOREIGN KEY(order_id) REFERENCES orders (id) ON DELETE SET NULL,
	FOREIGN KEY(strategy_id) REFERENCES strategies (id) ON DELETE SET NULL
)
""")
    op.execute("""
CREATE TABLE trade_journals (
	id UUID NOT NULL,
	user_id UUID NOT NULL,
	trading_account_id UUID,
	trade_id UUID,
	title VARCHAR(200) NOT NULL,
	content TEXT,
	mood VARCHAR(50),
	session_date DATE NOT NULL,
	pnl NUMERIC,
	tags JSONB,
	metadata JSONB,
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
	updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
	deleted_at TIMESTAMP WITH TIME ZONE,
	PRIMARY KEY (id),
	FOREIGN KEY(user_id) REFERENCES users (id) ON DELETE CASCADE,
	FOREIGN KEY(trading_account_id) REFERENCES trading_accounts (id) ON DELETE SET NULL,
	FOREIGN KEY(trade_id) REFERENCES trades (id) ON DELETE SET NULL
)
""")
    op.execute("""
CREATE INDEX ix_api_keys_user_id_deleted_at
ON api_keys (user_id, deleted_at)
""")
    op.execute("""
CREATE INDEX ix_api_keys_key_prefix
ON api_keys (key_prefix)
""")
    op.execute("""
CREATE INDEX ix_audit_logs_action_created_at
ON audit_logs (action, created_at)
""")
    op.execute("""
CREATE INDEX ix_audit_logs_resource
ON audit_logs (resource_type, resource_id)
""")
    op.execute("""
CREATE INDEX ix_audit_logs_user_id_created_at
ON audit_logs (user_id, created_at)
""")
    op.execute("""
CREATE INDEX ix_broker_connections_user_id
ON broker_connections (user_id)
""")
    op.execute("""
CREATE INDEX ix_notes_user_id_entity
ON notes (user_id, entity_type, entity_id)
""")
    op.execute("""
CREATE INDEX ix_notifications_user_id_read_at_created_at
ON notifications (user_id, read_at, created_at)
""")
    op.execute("""
CREATE INDEX ix_oauth_accounts_user_id
ON oauth_accounts (user_id)
""")
    op.execute("""
CREATE INDEX ix_sessions_user_id
ON sessions (user_id)
""")
    op.execute("""
CREATE INDEX ix_strategies_user_id_deleted_at
ON strategies (user_id, deleted_at)
""")
    op.execute("""
CREATE INDEX ix_subscriptions_user_id
ON subscriptions (user_id)
""")
    op.execute("""
CREATE INDEX ix_subscriptions_plan_id
ON subscriptions (plan_id)
""")
    op.execute("""
CREATE INDEX ix_user_roles_user_id
ON user_roles (user_id)
""")
    op.execute("""
CREATE INDEX ix_user_roles_role_id
ON user_roles (role_id)
""")
    op.execute("""
CREATE INDEX ix_billing_events_user_id
ON billing_events (user_id)
""")
    op.execute("""
CREATE INDEX ix_billing_events_subscription_id
ON billing_events (subscription_id)
""")
    op.execute("""
CREATE INDEX ix_trading_accounts_broker_connection_id_deleted_at
ON trading_accounts (broker_connection_id, deleted_at)
""")
    op.execute("""
CREATE INDEX ix_trading_accounts_user_id_deleted_at
ON trading_accounts (user_id, deleted_at)
""")
    op.execute("""
CREATE INDEX ix_orders_user_id_created_at
ON orders (user_id, created_at)
""")
    op.execute("""
CREATE INDEX ix_orders_trading_account_id_status_created_at
ON orders (trading_account_id, status, created_at)
""")
    op.execute("""
CREATE INDEX ix_positions_trading_account_id_deleted_at
ON positions (trading_account_id, deleted_at)
""")
    op.execute("""
CREATE INDEX ix_risk_rules_user_id_deleted_at
ON risk_rules (user_id, deleted_at)
""")
    op.execute("""
CREATE INDEX ix_trades_user_id_opened_at
ON trades (user_id, opened_at)
""")
    op.execute("""
CREATE INDEX ix_trades_trading_account_id_status_opened_at
ON trades (trading_account_id, status, opened_at)
""")
    op.execute("""
CREATE INDEX ix_trade_journals_user_id_session_date
ON trade_journals (user_id, session_date)
""")
    op.execute("""
CREATE UNIQUE INDEX uq_users_email_active
ON users (email)
WHERE deleted_at IS NULL
""")
    op.execute("""
CREATE UNIQUE INDEX uq_trading_accounts_external_active
ON trading_accounts (broker_connection_id, external_account_id)
WHERE deleted_at IS NULL
""")
    op.execute("""
CREATE UNIQUE INDEX uq_positions_account_symbol_active
ON positions (trading_account_id, symbol)
WHERE deleted_at IS NULL
""")


def downgrade() -> None:
    tables = [
        "trade_journals",
        "trades",
        "risk_rules",
        "positions",
        "orders",
        "trading_accounts",
        "billing_events",
        "user_roles",
        "subscriptions",
        "strategies",
        "sessions",
        "oauth_accounts",
        "notifications",
        "notes",
        "broker_connections",
        "audit_logs",
        "api_keys",
        "users",
        "roles",
        "plans",
    ]
    for name in tables:
        op.drop_table(name)
