"""SaaS billing — plans, coupons, invoices, usage tracking."""

from collections.abc import Sequence

from alembic import op

revision: str = "008_billing_saas"
down_revision: str | None = "007_notification_services"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

FREE_PLAN_FEATURES = '{"paper_trading": true, "analytics": "basic", "support": "community"}'
PRO_PLAN_FEATURES = (
    '{"copy_trading": true, "risk_engine": true, "analytics": "advanced", "support": "email"}'
)
ENTERPRISE_PLAN_FEATURES = (
    '{"copy_trading": true, "risk_engine": true, '
    '"analytics": "enterprise", "api_access": true, '
    '"support": "priority"}'
)


def upgrade() -> None:
    op.execute("""
ALTER TABLE plans
ADD COLUMN IF NOT EXISTS stripe_product_id VARCHAR(255),
ADD COLUMN IF NOT EXISTS max_copy_groups INTEGER NOT NULL DEFAULT 3,
ADD COLUMN IF NOT EXISTS trial_days INTEGER NOT NULL DEFAULT 0
""")
    op.execute(
        """
UPDATE plans SET
    code = 'free',
    name = 'Free',
    description = 'Paper trading with basic analytics',
    price_cents = 0,
    max_trading_accounts = 2,
    max_broker_connections = 1,
    max_copy_groups = 1,
    trial_days = 0,
    features = '"""
        + FREE_PLAN_FEATURES
        + """'::jsonb
WHERE code = 'starter'
""",
    )
    op.execute(
        """
UPDATE plans SET
    description = 'Advanced copy trading, risk engine, and analytics',
    max_trading_accounts = 10,
    max_broker_connections = 5,
    max_copy_groups = 5,
    trial_days = 14,
    features = '"""
        + PRO_PLAN_FEATURES
        + """'::jsonb
WHERE code = 'pro'
""",
    )
    op.execute(
        """
UPDATE plans SET
    code = 'enterprise',
    name = 'Enterprise',
    description = 'Unlimited scale, API access, and priority support',
    price_cents = 19900,
    max_trading_accounts = 100,
    max_broker_connections = 25,
    max_copy_groups = 50,
    trial_days = 14,
    features = '"""
        + ENTERPRISE_PLAN_FEATURES
        + """'::jsonb
WHERE code = 'scale'
""",
    )
    op.execute("""
CREATE TABLE coupons (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    code VARCHAR(50) NOT NULL,
    name VARCHAR(100) NOT NULL,
    stripe_coupon_id VARCHAR(255),
    stripe_promotion_code_id VARCHAR(255),
    discount_type VARCHAR(20) NOT NULL,
    percent_off INTEGER,
    amount_off_cents INTEGER,
    currency VARCHAR(3),
    duration VARCHAR(20) NOT NULL,
    duration_in_months INTEGER,
    max_redemptions INTEGER,
    times_redeemed INTEGER NOT NULL DEFAULT 0,
    active BOOLEAN NOT NULL DEFAULT true,
    expires_at TIMESTAMPTZ,
    applicable_plan_codes JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    deleted_at TIMESTAMPTZ,
    CONSTRAINT uq_coupons_code UNIQUE (code)
)
""")
    op.execute("""
CREATE TABLE invoices (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    subscription_id UUID REFERENCES subscriptions(id) ON DELETE SET NULL,
    stripe_invoice_id VARCHAR(255) NOT NULL,
    invoice_number VARCHAR(100),
    status VARCHAR(30) NOT NULL,
    amount_due_cents INTEGER NOT NULL DEFAULT 0,
    amount_paid_cents INTEGER NOT NULL DEFAULT 0,
    currency VARCHAR(3) NOT NULL DEFAULT 'USD',
    hosted_invoice_url VARCHAR(500),
    invoice_pdf_url VARCHAR(500),
    period_start TIMESTAMPTZ,
    period_end TIMESTAMPTZ,
    paid_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT uq_invoices_stripe_id UNIQUE (stripe_invoice_id)
)
""")
    op.execute("CREATE INDEX ix_invoices_user_id ON invoices (user_id)")
    op.execute("""
CREATE TABLE usage_records (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    metric VARCHAR(50) NOT NULL,
    quantity INTEGER NOT NULL DEFAULT 0,
    period_start TIMESTAMPTZ NOT NULL,
    period_end TIMESTAMPTZ NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT uq_usage_records_user_metric_period
        UNIQUE (user_id, metric, period_start)
)
""")
    op.execute("CREATE INDEX ix_usage_records_user_id ON usage_records (user_id)")
    op.execute("""
ALTER TABLE subscriptions
ADD COLUMN coupon_id UUID REFERENCES coupons(id) ON DELETE SET NULL,
ADD COLUMN stripe_coupon_id VARCHAR(255)
""")


def downgrade() -> None:
    op.execute("""
ALTER TABLE subscriptions
DROP COLUMN IF EXISTS stripe_coupon_id,
DROP COLUMN IF EXISTS coupon_id
""")
    op.execute("DROP TABLE IF EXISTS usage_records")
    op.execute("DROP TABLE IF EXISTS invoices")
    op.execute("DROP TABLE IF EXISTS coupons")
    op.execute("""
ALTER TABLE plans
DROP COLUMN IF EXISTS trial_days,
DROP COLUMN IF EXISTS max_copy_groups,
DROP COLUMN IF EXISTS stripe_product_id
""")
