"""Extend risk_rules and add breach/snapshot tables."""

from collections.abc import Sequence

from alembic import op

revision: str = "005_risk_engine"
down_revision: str | None = "004_copy_trading"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute("""
ALTER TABLE risk_rules
ADD COLUMN name VARCHAR(100) NOT NULL DEFAULT 'Default',
ADD COLUMN enabled BOOLEAN NOT NULL DEFAULT true,
ADD COLUMN max_position_size_usd NUMERIC(18, 2),
ADD COLUMN max_leverage NUMERIC(8, 2),
ADD COLUMN allowed_symbols JSONB,
ADD COLUMN blocked_symbols JSONB,
ADD COLUMN trading_hours_start TIME WITHOUT TIME ZONE,
ADD COLUMN trading_hours_end TIME WITHOUT TIME ZONE,
ADD COLUMN trading_hours_timezone VARCHAR(50) DEFAULT 'America/New_York',
ADD COLUMN kill_switch_active BOOLEAN NOT NULL DEFAULT false,
ADD COLUMN auto_flatten_on_breach BOOLEAN NOT NULL DEFAULT true,
ADD COLUMN auto_stop_copying_on_breach BOOLEAN NOT NULL DEFAULT true
""")
    op.execute("""
CREATE INDEX ix_risk_rules_trading_account_id ON risk_rules (trading_account_id)
""")

    op.execute("""
CREATE TABLE risk_breaches (
    id UUID NOT NULL,
    user_id UUID NOT NULL,
    risk_rule_id UUID,
    trading_account_id UUID NOT NULL,
    breach_type VARCHAR(30) NOT NULL,
    action_taken VARCHAR(30) NOT NULL,
    message TEXT NOT NULL,
    current_value NUMERIC(18, 4),
    limit_value NUMERIC(18, 4),
    symbol VARCHAR(50),
    resolved_at TIMESTAMP WITH TIME ZONE,
    metadata JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
    PRIMARY KEY (id),
    FOREIGN KEY(user_id) REFERENCES users (id) ON DELETE CASCADE,
    FOREIGN KEY(risk_rule_id) REFERENCES risk_rules (id) ON DELETE SET NULL,
    FOREIGN KEY(trading_account_id) REFERENCES trading_accounts (id) ON DELETE CASCADE
)
""")
    op.execute("""
CREATE INDEX ix_risk_breaches_account_created
ON risk_breaches (trading_account_id, created_at)
""")
    op.execute("""
CREATE INDEX ix_risk_breaches_user_id_created
ON risk_breaches (user_id, created_at)
""")
    op.execute("""
CREATE INDEX ix_risk_breaches_type ON risk_breaches (breach_type)
""")

    op.execute("""
CREATE TABLE risk_monitor_snapshots (
    id UUID NOT NULL,
    trading_account_id UUID NOT NULL,
    status VARCHAR(20) NOT NULL,
    daily_pnl NUMERIC(18, 2),
    drawdown_usd NUMERIC(18, 2),
    peak_equity NUMERIC(18, 2),
    current_equity NUMERIC(18, 2),
    total_open_contracts INTEGER,
    current_leverage NUMERIC(8, 2),
    kill_switch_active BOOLEAN NOT NULL DEFAULT false,
    metadata JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
    PRIMARY KEY (id),
    FOREIGN KEY(trading_account_id) REFERENCES trading_accounts (id) ON DELETE CASCADE
)
""")
    op.execute("""
CREATE INDEX ix_risk_snapshots_account_created
ON risk_monitor_snapshots (trading_account_id, created_at)
""")


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS risk_monitor_snapshots")
    op.execute("DROP TABLE IF EXISTS risk_breaches")
    op.execute("DROP INDEX IF EXISTS ix_risk_rules_trading_account_id")
    op.execute("""
ALTER TABLE risk_rules
DROP COLUMN IF EXISTS name,
DROP COLUMN IF EXISTS enabled,
DROP COLUMN IF EXISTS max_position_size_usd,
DROP COLUMN IF EXISTS max_leverage,
DROP COLUMN IF EXISTS allowed_symbols,
DROP COLUMN IF EXISTS blocked_symbols,
DROP COLUMN IF EXISTS trading_hours_start,
DROP COLUMN IF EXISTS trading_hours_end,
DROP COLUMN IF EXISTS trading_hours_timezone,
DROP COLUMN IF EXISTS kill_switch_active,
DROP COLUMN IF EXISTS auto_flatten_on_breach,
DROP COLUMN IF EXISTS auto_stop_copying_on_breach
""")
