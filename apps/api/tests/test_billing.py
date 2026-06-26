"""Billing and entitlements tests."""

from __future__ import annotations

from tradeflow.core.config import get_settings
from tradeflow.db.enums import CouponDiscountType, CouponDuration, PlanInterval
from tradeflow.features.billing.schemas import AdminCreateCouponRequest, PlanResponse
from tradeflow.integrations.stripe.client import StripeClient


def test_stripe_dev_mode_checkout() -> None:
    settings = get_settings()
    client = StripeClient(settings)
    assert not client.enabled
    url = client.create_checkout_session(
        customer_id="cus_dev_test",
        price_id="price_dev_pro",
        success_url=settings.billing_success_url,
        cancel_url=settings.billing_cancel_url,
        trial_days=14,
        metadata={"plan_code": "pro"},
    )
    assert "checkout=success" in url
    assert "plan=pro" in url


def test_stripe_dev_create_customer() -> None:
    settings = get_settings()
    client = StripeClient(settings)
    customer_id = client.create_customer(email="test@example.com", name="Test User")
    assert customer_id.startswith("cus_dev_")


def test_plan_response_schema() -> None:
    from uuid import uuid4

    plan = PlanResponse(
        id=uuid4(),
        code="pro",
        name="Pro",
        description="Pro plan",
        price_cents=7900,
        currency="USD",
        interval=PlanInterval.MONTH,
        max_trading_accounts=10,
        max_broker_connections=5,
        max_copy_groups=5,
        trial_days=14,
        features={"analytics": "advanced"},
        is_active=True,
    )
    assert plan.code == "pro"
    assert plan.trial_days == 14


def test_admin_coupon_request_validation() -> None:
    req = AdminCreateCouponRequest(
        code="LAUNCH20",
        name="Launch 20% off",
        discount_type=CouponDiscountType.PERCENT,
        percent_off=20,
        duration=CouponDuration.ONCE,
    )
    assert req.code == "LAUNCH20"
    assert req.percent_off == 20
