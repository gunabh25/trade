"""Stripe billing — subscriptions, checkout, webhooks, coupons, admin."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from tradeflow.core.config import Settings
from tradeflow.core.errors import ConflictError, NotFoundError
from tradeflow.core.logging import get_logger
from tradeflow.db.enums import (
    BillingEventStatus,
    BillingEventType,
    InvoiceStatus,
    SubscriptionStatus,
)
from tradeflow.db.models.billing import BillingEvent, Coupon, Invoice, Plan, Subscription
from tradeflow.db.models.user import User
from tradeflow.features.billing.entitlements import EntitlementService
from tradeflow.features.billing.schemas import (
    AdminCreateCouponRequest,
    AdminSubscriptionResponse,
    AdminUpdatePlanRequest,
    AdminUpdateSubscriptionRequest,
    BillingOverviewResponse,
    CheckoutRequest,
    CheckoutResponse,
    CouponResponse,
    InvoiceResponse,
    PlanResponse,
    PortalResponse,
    SubscriptionResponse,
)
from tradeflow.integrations.stripe.client import StripeClient
from tradeflow.notifications.dispatcher import NotificationDispatcher

logger = get_logger(__name__)

ACTIVE_STATUSES = {
    SubscriptionStatus.ACTIVE,
    SubscriptionStatus.TRIALING,
    SubscriptionStatus.PAST_DUE,
}


class BillingService:
    """SaaS billing orchestration with Stripe and entitlements."""

    def __init__(
        self,
        settings: Settings,
        stripe_client: StripeClient,
        entitlements: EntitlementService,
        notification_dispatcher: NotificationDispatcher | None = None,
    ) -> None:
        self._settings = settings
        self._stripe = stripe_client
        self._entitlements = entitlements
        self._notifications = notification_dispatcher

    async def list_plans(self, db: AsyncSession) -> list[PlanResponse]:
        rows = await db.scalars(
            select(Plan).where(Plan.is_active.is_(True), Plan.deleted_at.is_(None)),
        )
        return [PlanResponse.model_validate(row) for row in rows.all()]

    async def get_billing_overview(
        self,
        db: AsyncSession,
        user: User,
    ) -> BillingOverviewResponse:
        subscription = await self.ensure_subscription(db, user)
        usage = await self._entitlements.get_usage_summary(db, user.id)
        coupon_code = None
        if subscription.coupon_id:
            coupon = await db.get(Coupon, subscription.coupon_id)
            coupon_code = coupon.code if coupon else None
        is_trialing = subscription.status == SubscriptionStatus.TRIALING
        return BillingOverviewResponse(
            subscription=SubscriptionResponse(
                id=subscription.id,
                status=subscription.status,
                plan=PlanResponse.model_validate(subscription.plan),
                trial_ends_at=subscription.trial_ends_at,
                current_period_start=subscription.current_period_start,
                current_period_end=subscription.current_period_end,
                canceled_at=subscription.canceled_at,
                coupon_code=coupon_code,
                is_trialing=is_trialing,
            ),
            usage=usage,
            stripe_enabled=self._stripe.enabled,
            publishable_key=self._settings.stripe_publishable_key,
        )

    async def ensure_subscription(self, db: AsyncSession, user: User) -> Subscription:
        subscription = await self._entitlements.get_active_subscription(db, user.id)
        if subscription is not None:
            return subscription

        free_plan = await self._entitlements.get_plan_by_code(db, "free")
        if free_plan is None:
            raise NotFoundError("Free plan is not configured")

        now = datetime.now(tz=UTC)
        subscription = Subscription(
            user_id=user.id,
            plan_id=free_plan.id,
            status=SubscriptionStatus.ACTIVE,
            current_period_start=now,
            current_period_end=now + timedelta(days=365 * 10),
        )
        db.add(subscription)
        await db.flush()
        await db.refresh(subscription, attribute_names=["plan"])
        return subscription

    async def create_checkout(
        self,
        db: AsyncSession,
        user: User,
        request: CheckoutRequest,
    ) -> CheckoutResponse:
        if request.plan_code == "free":
            raise ConflictError("Free plan does not require checkout")

        plan = await self._entitlements.get_plan_by_code(db, request.plan_code)
        if plan is None or not plan.is_active:
            raise NotFoundError(f"Plan '{request.plan_code}' not found")

        promotion_code = None
        coupon = None
        if request.coupon_code:
            coupon = await self._get_valid_coupon(db, request.coupon_code, request.plan_code)
            promotion_code = coupon.stripe_promotion_code_id

        customer_id = await self._ensure_stripe_customer(db, user)
        price_id = plan.stripe_price_id or f"price_dev_{plan.code}"
        trial_days = plan.trial_days or self._settings.stripe_trial_days_default

        url = self._stripe.create_checkout_session(
            customer_id=customer_id,
            price_id=price_id,
            success_url=self._settings.billing_success_url,
            cancel_url=self._settings.billing_cancel_url,
            trial_days=trial_days,
            promotion_code=promotion_code,
            metadata={"user_id": str(user.id), "plan_code": plan.code},
        )
        if coupon is not None:
            logger.info("checkout_with_coupon", user_id=str(user.id), coupon=coupon.code)
        return CheckoutResponse(checkout_url=url)

    async def create_portal(self, db: AsyncSession, user: User) -> PortalResponse:
        if not user.stripe_customer_id:
            raise ConflictError("No Stripe customer — subscribe to a paid plan first")
        url = self._stripe.create_portal_session(
            customer_id=user.stripe_customer_id,
            return_url=f"{self._settings.frontend_url.rstrip('/')}/dashboard/billing",
        )
        return PortalResponse(portal_url=url)

    async def validate_coupon(
        self,
        db: AsyncSession,
        code: str,
        plan_code: str | None = None,
    ) -> CouponResponse:
        coupon = await self._get_valid_coupon(db, code, plan_code)
        return CouponResponse.model_validate(coupon)

    async def list_invoices(self, db: AsyncSession, user_id: UUID) -> list[InvoiceResponse]:
        rows = await db.scalars(
            select(Invoice)
            .where(Invoice.user_id == user_id)
            .order_by(Invoice.created_at.desc())
            .limit(50),
        )
        return [InvoiceResponse.model_validate(row) for row in rows.all()]

    async def handle_webhook(
        self,
        db: AsyncSession,
        payload: bytes,
        signature: str,
    ) -> dict[str, str]:
        event = self._stripe.construct_event(payload, signature)
        event_id = str(event.id)
        existing = await db.scalar(
            select(BillingEvent).where(BillingEvent.stripe_event_id == event_id),
        )
        if existing is not None:
            return {"status": "duplicate"}

        event_type = str(event.type)
        data_object = event.data.object

        if event_type == "checkout.session.completed":
            await self._handle_checkout_completed(db, data_object, event_id)
        elif event_type.startswith("customer.subscription."):
            await self._handle_subscription_event(db, data_object, event_type, event_id)
        elif event_type.startswith("invoice."):
            await self._handle_invoice_event(db, data_object, event_type, event_id)

        return {"status": "processed"}

    async def admin_list_subscriptions(
        self,
        db: AsyncSession,
        *,
        limit: int = 50,
    ) -> list[AdminSubscriptionResponse]:
        rows = await db.scalars(
            select(Subscription)
            .options(selectinload(Subscription.plan), selectinload(Subscription.user))
            .where(Subscription.deleted_at.is_(None))
            .order_by(Subscription.created_at.desc())
            .limit(limit),
        )
        results: list[AdminSubscriptionResponse] = []
        for row in rows.all():
            results.append(
                AdminSubscriptionResponse(
                    id=row.id,
                    user_id=row.user_id,
                    user_email=row.user.email,
                    status=row.status,
                    plan_code=row.plan.code,
                    plan_name=row.plan.name,
                    trial_ends_at=row.trial_ends_at,
                    current_period_end=row.current_period_end,
                    stripe_subscription_id=row.stripe_subscription_id,
                ),
            )
        return results

    async def admin_update_subscription(
        self,
        db: AsyncSession,
        subscription_id: UUID,
        request: AdminUpdateSubscriptionRequest,
    ) -> AdminSubscriptionResponse:
        subscription = await db.scalar(
            select(Subscription)
            .options(selectinload(Subscription.plan), selectinload(Subscription.user))
            .where(Subscription.id == subscription_id),
        )
        if subscription is None:
            raise NotFoundError("Subscription not found")

        if request.plan_code:
            plan = await self._entitlements.get_plan_by_code(db, request.plan_code)
            if plan is None:
                raise NotFoundError(f"Plan '{request.plan_code}' not found")
            subscription.plan_id = plan.id

        if request.status:
            subscription.status = request.status

        if request.extend_trial_days:
            base = subscription.trial_ends_at or datetime.now(tz=UTC)
            subscription.trial_ends_at = base + timedelta(days=request.extend_trial_days)
            subscription.status = SubscriptionStatus.TRIALING

        await db.flush()
        await db.refresh(subscription, attribute_names=["plan", "user"])
        return AdminSubscriptionResponse(
            id=subscription.id,
            user_id=subscription.user_id,
            user_email=subscription.user.email,
            status=subscription.status,
            plan_code=subscription.plan.code,
            plan_name=subscription.plan.name,
            trial_ends_at=subscription.trial_ends_at,
            current_period_end=subscription.current_period_end,
            stripe_subscription_id=subscription.stripe_subscription_id,
        )

    async def admin_create_coupon(
        self,
        db: AsyncSession,
        request: AdminCreateCouponRequest,
    ) -> CouponResponse:
        existing = await db.scalar(select(Coupon).where(Coupon.code == request.code.upper()))
        if existing is not None:
            raise ConflictError("Coupon code already exists")

        stripe_coupon_id, promo_id = self._stripe.create_coupon(
            name=request.name,
            percent_off=request.percent_off,
            amount_off_cents=request.amount_off_cents,
            duration=request.duration.value,
            duration_in_months=request.duration_in_months,
            max_redemptions=request.max_redemptions,
        )
        coupon = Coupon(
            code=request.code.upper(),
            name=request.name,
            stripe_coupon_id=stripe_coupon_id,
            stripe_promotion_code_id=promo_id,
            discount_type=request.discount_type,
            percent_off=request.percent_off,
            amount_off_cents=request.amount_off_cents,
            currency="USD",
            duration=request.duration,
            duration_in_months=request.duration_in_months,
            max_redemptions=request.max_redemptions,
            expires_at=request.expires_at,
            applicable_plan_codes=request.applicable_plan_codes,
        )
        db.add(coupon)
        await db.flush()
        return CouponResponse.model_validate(coupon)

    async def admin_update_plan(
        self,
        db: AsyncSession,
        plan_code: str,
        request: AdminUpdatePlanRequest,
    ) -> PlanResponse:
        plan = await self._entitlements.get_plan_by_code(db, plan_code)
        if plan is None:
            raise NotFoundError(f"Plan '{plan_code}' not found")

        if request.stripe_price_id is not None:
            plan.stripe_price_id = request.stripe_price_id
        if request.stripe_product_id is not None:
            plan.stripe_product_id = request.stripe_product_id
        if request.price_cents is not None:
            plan.price_cents = request.price_cents
        if request.trial_days is not None:
            plan.trial_days = request.trial_days
        if request.is_active is not None:
            plan.is_active = request.is_active
        if request.features is not None:
            plan.features = request.features

        await db.flush()
        return PlanResponse.model_validate(plan)

    async def _ensure_stripe_customer(self, db: AsyncSession, user: User) -> str:
        if user.stripe_customer_id:
            return user.stripe_customer_id
        name = " ".join(filter(None, [user.first_name, user.last_name])) or None
        customer_id = self._stripe.create_customer(
            email=user.email,
            name=name,
            metadata={"user_id": str(user.id)},
        )
        user.stripe_customer_id = customer_id
        await db.flush()
        return customer_id

    async def _get_valid_coupon(
        self,
        db: AsyncSession,
        code: str,
        plan_code: str | None,
    ) -> Coupon:
        coupon = await db.scalar(
            select(Coupon).where(
                Coupon.code == code.upper(),
                Coupon.active.is_(True),
                Coupon.deleted_at.is_(None),
            ),
        )
        if coupon is None:
            raise NotFoundError("Invalid coupon code")
        if coupon.expires_at and coupon.expires_at < datetime.now(tz=UTC):
            raise ConflictError("Coupon has expired")
        if coupon.max_redemptions and coupon.times_redeemed >= coupon.max_redemptions:
            raise ConflictError("Coupon redemption limit reached")
        if (
            plan_code
            and coupon.applicable_plan_codes
            and plan_code not in coupon.applicable_plan_codes
        ):
            raise ConflictError("Coupon not valid for this plan")
        return coupon

    async def _handle_checkout_completed(
        self,
        db: AsyncSession,
        session: Any,
        event_id: str,
    ) -> None:
        metadata = dict(session.get("metadata") or {})
        user_id = UUID(metadata["user_id"])
        plan_code = metadata.get("plan_code", "pro")
        user = await db.get(User, user_id)
        plan = await self._entitlements.get_plan_by_code(db, plan_code)
        if user is None or plan is None:
            return

        subscription = await self._entitlements.get_active_subscription(db, user_id)
        if subscription is None:
            subscription = Subscription(
                user_id=user_id,
                plan_id=plan.id,
                status=SubscriptionStatus.ACTIVE,
            )
            db.add(subscription)
        else:
            subscription.plan_id = plan.id

        subscription.stripe_subscription_id = session.get("subscription")
        await self._record_billing_event(
            db,
            user_id=user_id,
            subscription_id=subscription.id,
            event_type=BillingEventType.SUBSCRIPTION_CREATED,
            stripe_event_id=event_id,
        )
        await db.flush()

    async def _handle_subscription_event(
        self,
        db: AsyncSession,
        sub: Any,
        event_type: str,
        event_id: str,
    ) -> None:
        stripe_sub_id = str(sub.get("id", ""))
        subscription = await db.scalar(
            select(Subscription)
            .options(selectinload(Subscription.plan), selectinload(Subscription.user))
            .where(Subscription.stripe_subscription_id == stripe_sub_id),
        )
        if subscription is None:
            customer_id = sub.get("customer")
            user = await db.scalar(select(User).where(User.stripe_customer_id == customer_id))
            if user is None:
                return
            subscription = await self.ensure_subscription(db, user)
            subscription.stripe_subscription_id = stripe_sub_id

        status_map = {
            "trialing": SubscriptionStatus.TRIALING,
            "active": SubscriptionStatus.ACTIVE,
            "past_due": SubscriptionStatus.PAST_DUE,
            "canceled": SubscriptionStatus.CANCELED,
            "incomplete": SubscriptionStatus.INCOMPLETE,
        }
        subscription.status = status_map.get(str(sub.get("status")), SubscriptionStatus.ACTIVE)
        subscription.trial_ends_at = _ts(sub.get("trial_end"))
        subscription.current_period_start = _ts(sub.get("current_period_start"))
        subscription.current_period_end = _ts(sub.get("current_period_end"))
        if sub.get("canceled_at"):
            subscription.canceled_at = _ts(sub.get("canceled_at"))

        billing_type = BillingEventType.SUBSCRIPTION_UPDATED
        if event_type.endswith("deleted"):
            billing_type = BillingEventType.SUBSCRIPTION_CANCELED
            subscription.status = SubscriptionStatus.CANCELED
        elif subscription.status == SubscriptionStatus.TRIALING:
            billing_type = BillingEventType.TRIAL_STARTED

        await self._record_billing_event(
            db,
            user_id=subscription.user_id,
            subscription_id=subscription.id,
            event_type=billing_type,
            stripe_event_id=event_id,
        )

        if self._notifications and subscription.status == SubscriptionStatus.PAST_DUE:
            await self._notifications.notify_subscription_expiry(
                db,
                user_id=subscription.user_id,
                plan_name=subscription.plan.name,
                days_remaining=0,
                subscription_id=subscription.id,
            )

        await db.flush()

    async def _handle_invoice_event(
        self,
        db: AsyncSession,
        invoice: Any,
        event_type: str,
        event_id: str,
    ) -> None:
        stripe_invoice_id = str(invoice.get("id", ""))
        customer_id = invoice.get("customer")
        user = await db.scalar(select(User).where(User.stripe_customer_id == customer_id))
        if user is None:
            return

        status_map = {
            "draft": InvoiceStatus.DRAFT,
            "open": InvoiceStatus.OPEN,
            "paid": InvoiceStatus.PAID,
            "void": InvoiceStatus.VOID,
            "uncollectible": InvoiceStatus.UNCOLLECTIBLE,
        }
        inv_status = status_map.get(str(invoice.get("status")), InvoiceStatus.OPEN)
        existing = await db.scalar(
            select(Invoice).where(Invoice.stripe_invoice_id == stripe_invoice_id),
        )
        if existing is None:
            existing = Invoice(
                user_id=user.id,
                stripe_invoice_id=stripe_invoice_id,
                status=inv_status,
                amount_due_cents=int(invoice.get("amount_due") or 0),
                amount_paid_cents=int(invoice.get("amount_paid") or 0),
                currency=str(invoice.get("currency", "usd")).upper(),
            )
            db.add(existing)
        else:
            existing.status = inv_status
            existing.amount_due_cents = int(invoice.get("amount_due") or 0)
            existing.amount_paid_cents = int(invoice.get("amount_paid") or 0)

        existing.invoice_number = invoice.get("number")
        existing.hosted_invoice_url = invoice.get("hosted_invoice_url")
        existing.invoice_pdf_url = invoice.get("invoice_pdf")
        existing.period_start = _ts(invoice.get("period_start"))
        existing.period_end = _ts(invoice.get("period_end"))
        if inv_status == InvoiceStatus.PAID:
            existing.paid_at = _ts(invoice.get("status_transitions", {}).get("paid_at"))

        billing_type = (
            BillingEventType.INVOICE_PAID
            if event_type == "invoice.paid"
            else BillingEventType.INVOICE_FAILED
        )
        billing_status = (
            BillingEventStatus.SUCCEEDED
            if billing_type == BillingEventType.INVOICE_PAID
            else BillingEventStatus.FAILED
        )
        await self._record_billing_event(
            db,
            user_id=user.id,
            subscription_id=existing.subscription_id,
            event_type=billing_type,
            status=billing_status,
            amount_cents=existing.amount_paid_cents,
            currency=existing.currency,
            stripe_invoice_id=stripe_invoice_id,
            stripe_event_id=event_id,
        )
        await db.flush()

    async def _record_billing_event(
        self,
        db: AsyncSession,
        *,
        user_id: UUID,
        event_type: BillingEventType,
        stripe_event_id: str,
        subscription_id: UUID | None = None,
        status: BillingEventStatus = BillingEventStatus.SUCCEEDED,
        amount_cents: int | None = None,
        currency: str | None = None,
        stripe_invoice_id: str | None = None,
    ) -> None:
        db.add(
            BillingEvent(
                user_id=user_id,
                subscription_id=subscription_id,
                event_type=event_type,
                status=status,
                amount_cents=amount_cents,
                currency=currency,
                stripe_invoice_id=stripe_invoice_id,
                stripe_event_id=stripe_event_id,
            ),
        )


def _ts(value: Any) -> datetime | None:
    if value is None:
        return None
    return datetime.fromtimestamp(int(value), tz=UTC)
