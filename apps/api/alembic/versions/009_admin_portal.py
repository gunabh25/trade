"""Admin portal tables — tickets, flags, announcements, system logs."""

from collections.abc import Sequence

from alembic import op

revision: str = "009_admin_portal"
down_revision: str | None = "008_billing_saas"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute("""
CREATE TABLE support_tickets (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    assigned_to_id UUID REFERENCES users(id) ON DELETE SET NULL,
    subject VARCHAR(200) NOT NULL,
    description TEXT NOT NULL,
    status VARCHAR(30) NOT NULL DEFAULT 'open',
    priority VARCHAR(20) NOT NULL DEFAULT 'medium',
    resolved_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    deleted_at TIMESTAMPTZ
)
""")
    op.execute("CREATE INDEX ix_support_tickets_user_id ON support_tickets (user_id)")
    op.execute("CREATE INDEX ix_support_tickets_status ON support_tickets (status)")
    op.execute("""
CREATE TABLE feature_flags (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    key VARCHAR(100) NOT NULL UNIQUE,
    name VARCHAR(150) NOT NULL,
    description TEXT,
    enabled BOOLEAN NOT NULL DEFAULT false,
    rules JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
)
""")
    op.execute("""
CREATE TABLE announcements (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title VARCHAR(200) NOT NULL,
    body TEXT NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'draft',
    starts_at TIMESTAMPTZ,
    ends_at TIMESTAMPTZ,
    target_roles JSONB,
    created_by_id UUID REFERENCES users(id) ON DELETE SET NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    deleted_at TIMESTAMPTZ
)
""")
    op.execute("""
CREATE TABLE system_log_entries (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    level VARCHAR(20) NOT NULL,
    source VARCHAR(100) NOT NULL,
    message TEXT NOT NULL,
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    metadata JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
)
""")
    op.execute("CREATE INDEX ix_system_log_entries_level ON system_log_entries (level)")
    op.execute("CREATE INDEX ix_system_log_entries_source ON system_log_entries (source)")
    op.execute(
        "CREATE INDEX ix_system_log_entries_created_at ON system_log_entries (created_at)",
    )


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS system_log_entries")
    op.execute("DROP TABLE IF EXISTS announcements")
    op.execute("DROP TABLE IF EXISTS feature_flags")
    op.execute("DROP TABLE IF EXISTS support_tickets")
