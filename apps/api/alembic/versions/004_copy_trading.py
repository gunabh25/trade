"""Copy trading tables — groups, followers, events, mappings, execution logs."""

from collections.abc import Sequence

from alembic import op

revision: str = "004_copy_trading"
down_revision: str | None = "003_auth_system"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute("""
CREATE TABLE copy_groups (
    id UUID NOT NULL,
    user_id UUID NOT NULL,
    leader_account_id UUID NOT NULL,
    name VARCHAR(100) NOT NULL,
    mode VARCHAR(20) NOT NULL DEFAULT 'live',
    status VARCHAR(20) NOT NULL DEFAULT 'draft',
    copying_enabled BOOLEAN NOT NULL DEFAULT false,
    sim_validated BOOLEAN NOT NULL DEFAULT false,
    metadata JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
    deleted_at TIMESTAMP WITH TIME ZONE,
    PRIMARY KEY (id),
    FOREIGN KEY(user_id) REFERENCES users (id) ON DELETE CASCADE,
    FOREIGN KEY(leader_account_id) REFERENCES trading_accounts (id) ON DELETE RESTRICT
)
""")
    op.execute("""
CREATE INDEX ix_copy_groups_user_id_deleted_at ON copy_groups (user_id, deleted_at)
""")
    op.execute("""
CREATE INDEX ix_copy_groups_status ON copy_groups (status)
""")

    op.execute("""
CREATE TABLE copy_group_followers (
    id UUID NOT NULL,
    copy_group_id UUID NOT NULL,
    follower_account_id UUID NOT NULL,
    enabled BOOLEAN NOT NULL DEFAULT true,
    copy_mode VARCHAR(30) NOT NULL,
    sizing_value NUMERIC(18, 6) NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'active',
    locked_at TIMESTAMP WITH TIME ZONE,
    lock_reason VARCHAR(255),
    metadata JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
    deleted_at TIMESTAMP WITH TIME ZONE,
    PRIMARY KEY (id),
    FOREIGN KEY(copy_group_id) REFERENCES copy_groups (id) ON DELETE CASCADE,
    FOREIGN KEY(follower_account_id) REFERENCES trading_accounts (id) ON DELETE RESTRICT,
    UNIQUE (copy_group_id, follower_account_id)
)
""")
    op.execute("""
CREATE INDEX ix_copy_group_followers_status ON copy_group_followers (status)
""")

    op.execute("""
CREATE TABLE copy_events (
    id UUID NOT NULL,
    user_id UUID NOT NULL,
    copy_group_id UUID NOT NULL,
    leader_account_id UUID NOT NULL,
    follower_account_id UUID,
    leader_event_id VARCHAR(255) NOT NULL,
    leader_order_id VARCHAR(100),
    follower_order_id VARCHAR(100),
    action VARCHAR(20) NOT NULL,
    result VARCHAR(20) NOT NULL,
    symbol VARCHAR(50),
    quantity INTEGER,
    leader_price NUMERIC(18, 8),
    follower_price NUMERIC(18, 8),
    slippage NUMERIC(18, 8),
    latency_ms INTEGER,
    error_message TEXT,
    metadata JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
    PRIMARY KEY (id),
    FOREIGN KEY(user_id) REFERENCES users (id) ON DELETE CASCADE,
    FOREIGN KEY(copy_group_id) REFERENCES copy_groups (id) ON DELETE CASCADE,
    FOREIGN KEY(leader_account_id) REFERENCES trading_accounts (id) ON DELETE CASCADE,
    FOREIGN KEY(follower_account_id) REFERENCES trading_accounts (id) ON DELETE SET NULL
)
""")
    op.execute("""
CREATE INDEX ix_copy_events_group_created ON copy_events (copy_group_id, created_at)
""")
    op.execute("""
CREATE INDEX ix_copy_events_leader_event_id ON copy_events (leader_event_id)
""")
    op.execute("""
CREATE INDEX ix_copy_events_user_id_created ON copy_events (user_id, created_at)
""")

    op.execute("""
CREATE TABLE order_mappings (
    id UUID NOT NULL,
    copy_group_id UUID NOT NULL,
    leader_order_id VARCHAR(100) NOT NULL,
    follower_account_id UUID NOT NULL,
    follower_order_id VARCHAR(100) NOT NULL,
    leader_order_db_id UUID,
    follower_order_db_id UUID,
    leg_type VARCHAR(20) NOT NULL DEFAULT 'entry',
    metadata JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
    PRIMARY KEY (id),
    FOREIGN KEY(copy_group_id) REFERENCES copy_groups (id) ON DELETE CASCADE,
    FOREIGN KEY(follower_account_id) REFERENCES trading_accounts (id) ON DELETE CASCADE,
    FOREIGN KEY(leader_order_db_id) REFERENCES orders (id) ON DELETE SET NULL,
    FOREIGN KEY(follower_order_db_id) REFERENCES orders (id) ON DELETE SET NULL,
    UNIQUE (copy_group_id, leader_order_id, follower_account_id, leg_type)
)
""")
    op.execute("""
CREATE INDEX ix_order_mappings_leader_order ON order_mappings (copy_group_id, leader_order_id)
""")

    op.execute("""
CREATE TABLE execution_logs (
    id UUID NOT NULL,
    user_id UUID NOT NULL,
    copy_group_id UUID NOT NULL,
    follower_account_id UUID NOT NULL,
    leader_event_id VARCHAR(255) NOT NULL,
    leader_order_id VARCHAR(100),
    action VARCHAR(20) NOT NULL,
    status VARCHAR(20) NOT NULL,
    attempt INTEGER NOT NULL DEFAULT 1,
    max_attempts INTEGER NOT NULL DEFAULT 5,
    next_retry_at TIMESTAMP WITH TIME ZONE,
    payload JSONB,
    result JSONB,
    error_message TEXT,
    latency_ms INTEGER,
    completed_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
    PRIMARY KEY (id),
    FOREIGN KEY(user_id) REFERENCES users (id) ON DELETE CASCADE,
    FOREIGN KEY(copy_group_id) REFERENCES copy_groups (id) ON DELETE CASCADE,
    FOREIGN KEY(follower_account_id) REFERENCES trading_accounts (id) ON DELETE CASCADE
)
""")
    op.execute("""
CREATE INDEX ix_execution_logs_status_created ON execution_logs (status, created_at)
""")
    op.execute("""
CREATE INDEX ix_execution_logs_copy_group_id ON execution_logs (copy_group_id, created_at)
""")
    op.execute("""
CREATE INDEX ix_execution_logs_leader_event_id ON execution_logs (leader_event_id)
""")


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS execution_logs")
    op.execute("DROP TABLE IF EXISTS order_mappings")
    op.execute("DROP TABLE IF EXISTS copy_events")
    op.execute("DROP TABLE IF EXISTS copy_group_followers")
    op.execute("DROP TABLE IF EXISTS copy_groups")
