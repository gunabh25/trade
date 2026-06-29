"""Production query-performance indexes."""

from collections.abc import Sequence

from alembic import op

revision: str = "013_production_indexes"
down_revision: str | None = "012_admin_enterprise"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute("""
CREATE INDEX IF NOT EXISTS ix_notification_deliveries_status_created_at
    ON notification_deliveries (status, created_at DESC)
""")
    op.execute("""
CREATE INDEX IF NOT EXISTS ix_subscriptions_status_deleted_at
    ON subscriptions (status, deleted_at)
    WHERE deleted_at IS NULL
""")
    op.execute("""
CREATE INDEX IF NOT EXISTS ix_usage_records_user_metric_period
    ON usage_records (user_id, metric, period_start DESC)
""")


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_usage_records_user_metric_period")
    op.execute("DROP INDEX IF EXISTS ix_subscriptions_status_deleted_at")
    op.execute("DROP INDEX IF EXISTS ix_notification_deliveries_status_created_at")
