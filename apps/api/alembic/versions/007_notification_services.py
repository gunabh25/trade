"""Notification channel settings, preferences, and new notification types."""

from collections.abc import Sequence

from alembic import op

revision: str = "007_notification_services"
down_revision: str | None = "006_journal_enhancements"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute("""
CREATE TABLE notification_channel_settings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    channel VARCHAR(20) NOT NULL,
    enabled BOOLEAN NOT NULL DEFAULT true,
    config JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT uq_notification_channel_user UNIQUE (user_id, channel)
)
""")
    op.execute("""
CREATE INDEX ix_notification_channel_settings_user_id
ON notification_channel_settings (user_id)
""")
    op.execute("""
CREATE TABLE notification_preferences (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    event_type VARCHAR(50) NOT NULL,
    channel VARCHAR(20) NOT NULL,
    enabled BOOLEAN NOT NULL DEFAULT true,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT uq_notification_preference_user_event_channel
        UNIQUE (user_id, event_type, channel)
)
""")
    op.execute("""
CREATE INDEX ix_notification_preferences_user_id ON notification_preferences (user_id)
""")


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS notification_preferences")
    op.execute("DROP TABLE IF EXISTS notification_channel_settings")
