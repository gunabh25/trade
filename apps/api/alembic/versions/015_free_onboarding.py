"""Allow free-tier paper onboarding: copy trading + two broker connections."""

from collections.abc import Sequence

from alembic import op

revision: str = "015_free_onboarding"
down_revision: str | None = "014_ai_platform"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute("""
UPDATE plans
SET
    max_broker_connections = GREATEST(max_broker_connections, 2),
    features = COALESCE(features, '{}'::jsonb) || '{"copy_trading": true}'::jsonb
WHERE code = 'free'
""")


def downgrade() -> None:
    op.execute("""
UPDATE plans
SET
    max_broker_connections = 1,
    features = COALESCE(features, '{}'::jsonb) - 'copy_trading'
WHERE code = 'free'
""")
