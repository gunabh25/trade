"""Billing API schemas."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from tradeflow.db.enums import (
    CouponDiscountType,
    CouponDuration,
    InvoiceStatus,
    PlanInterval,
    SubscriptionStatus,
    UsageMetric,
)


class PlanResponse(BaseModel):
    id: UUID
    code: str
    name: str
    description: str | None
    price_cents: int
    currency: str
    interval: PlanInterval
    max_trading_accounts: int
    max_broker_connections: int
    max_copy_groups: int
    trial_days: int
    features: dict[str, object] | None
    is_active: bool

    model_config = {"from_attributes": True}


class UsageItemResponse(BaseModel):
    metric: UsageMetric
    used: int
    limit: int
    percent: float


class SubscriptionResponse(BaseModel):
    id: UUID
    status: SubscriptionStatus
    plan: PlanResponse
    trial_ends_at: datetime | None
    current_period_start: datetime | None
    current_period_end: datetime | None
    canceled_at: datetime | None
    coupon_code: str | None = None
    is_trialing: bool = False


class BillingOverviewResponse(BaseModel):
    subscription: SubscriptionResponse
    usage: list[UsageItemResponse]
    stripe_enabled: bool
    publishable_key: str | None


class CheckoutRequest(BaseModel):
    plan_code: str = Field(description="Plan code: pro or enterprise")
    coupon_code: str | None = None


class CheckoutResponse(BaseModel):
    checkout_url: str


class PortalResponse(BaseModel):
    portal_url: str


class ValidateCouponRequest(BaseModel):
    code: str
    plan_code: str | None = None


class CouponResponse(BaseModel):
    id: UUID
    code: str
    name: str
    discount_type: CouponDiscountType
    percent_off: int | None
    amount_off_cents: int | None
    currency: str | None
    duration: CouponDuration
    active: bool
    expires_at: datetime | None

    model_config = {"from_attributes": True}


class InvoiceResponse(BaseModel):
    id: UUID
    stripe_invoice_id: str
    invoice_number: str | None
    status: InvoiceStatus
    amount_due_cents: int
    amount_paid_cents: int
    currency: str
    hosted_invoice_url: str | None
    invoice_pdf_url: str | None
    period_start: datetime | None
    period_end: datetime | None
    paid_at: datetime | None
    created_at: datetime

    model_config = {"from_attributes": True}


class AdminCreateCouponRequest(BaseModel):
    code: str = Field(min_length=3, max_length=50)
    name: str
    discount_type: CouponDiscountType
    percent_off: int | None = Field(default=None, ge=1, le=100)
    amount_off_cents: int | None = Field(default=None, ge=1)
    duration: CouponDuration = CouponDuration.ONCE
    duration_in_months: int | None = None
    max_redemptions: int | None = None
    expires_at: datetime | None = None
    applicable_plan_codes: list[str] | None = None


class AdminUpdatePlanRequest(BaseModel):
    stripe_price_id: str | None = None
    stripe_product_id: str | None = None
    price_cents: int | None = None
    trial_days: int | None = None
    is_active: bool | None = None
    features: dict[str, object] | None = None


class AdminSubscriptionResponse(BaseModel):
    id: UUID
    user_id: UUID
    user_email: str
    status: SubscriptionStatus
    plan_code: str
    plan_name: str
    trial_ends_at: datetime | None
    current_period_end: datetime | None
    stripe_subscription_id: str | None


class AdminUpdateSubscriptionRequest(BaseModel):
    plan_code: str | None = None
    status: SubscriptionStatus | None = None
    extend_trial_days: int | None = Field(default=None, ge=1, le=90)
