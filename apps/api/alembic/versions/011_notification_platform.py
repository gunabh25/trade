"""Notification platform — digest queue, delivery log, user settings."""

from collections.abc import Sequence

from alembic import op

revision: str = "011_notification_platform"
down_revision: str | None = "010_journal_production"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute("""
CREATE TABLE notification_user_settings (
    user_id UUID PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
    muted_until TIMESTAMPTZ,
    digest_enabled BOOLEAN NOT NULL DEFAULT FALSE,
    digest_frequency VARCHAR(20) NOT NULL DEFAULT 'daily',
    digest_hour_utc INTEGER NOT NULL DEFAULT 8,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
)
""")
    op.execute("""
CREATE TABLE notification_deliveries (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    event_type VARCHAR(50) NOT NULL,
    channel VARCHAR(20) NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'pending',
    attempts INTEGER NOT NULL DEFAULT 0,
    last_error TEXT,
    payload JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
)
""")
    op.execute("""
CREATE INDEX ix_notification_deliveries_user_id_status
ON notification_deliveries (user_id, status)
""")
    op.execute("""
CREATE TABLE notification_digest_queue (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    event_type VARCHAR(50) NOT NULL,
    channel VARCHAR(20) NOT NULL,
    title VARCHAR(255) NOT NULL,
    body TEXT NOT NULL,
    rendered JSONB NOT NULL,
    delivered_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
)
""")
    op.execute("""
CREATE INDEX ix_notification_digest_queue_user_pending
ON notification_digest_queue (user_id)
WHERE delivered_at IS NULL
""")


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS notification_digest_queue")
    op.execute("DROP TABLE IF EXISTS notification_deliveries")
    op.execute("DROP TABLE IF EXISTS notification_user_settings")
