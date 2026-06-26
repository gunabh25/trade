"""Thin Stripe SDK wrapper with development-mode fallbacks."""

from __future__ import annotations

from typing import Any

from tradeflow.core.config import Settings
from tradeflow.core.logging import get_logger

logger = get_logger(__name__)


class StripeClient:
    """Stripe API client — logs and returns mock data when keys are unset."""

    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._enabled = settings.stripe_enabled
        if self._enabled:
            import stripe

            stripe.api_key = settings.stripe_secret_key
            self._stripe = stripe
        else:
            self._stripe = None
            logger.info("stripe_dev_mode")

    @property
    def enabled(self) -> bool:
        return self._enabled

    def create_customer(
        self,
        *,
        email: str,
        name: str | None,
        metadata: dict[str, str] | None = None,
    ) -> str:
        if not self._enabled or self._stripe is None:
            customer_id = f"cus_dev_{email.replace('@', '_at_')}"
            logger.info("stripe_dev_create_customer", email=email, customer_id=customer_id)
            return customer_id

        customer = self._stripe.Customer.create(
            email=email,
            name=name,
            metadata=metadata or {},
        )
        return str(customer.id)

    def create_checkout_session(
        self,
        *,
        customer_id: str,
        price_id: str,
        success_url: str,
        cancel_url: str,
        trial_days: int = 0,
        promotion_code: str | None = None,
        metadata: dict[str, str] | None = None,
    ) -> str:
        if not self._enabled or self._stripe is None:
            plan_code = (metadata or {}).get("plan_code", "pro")
            url = f"{self._settings.billing_success_url}&plan={plan_code}&dev=1"
            logger.info("stripe_dev_checkout", customer_id=customer_id, url=url)
            return url

        params: dict[str, Any] = {
            "customer": customer_id,
            "mode": "subscription",
            "line_items": [{"price": price_id, "quantity": 1}],
            "success_url": success_url,
            "cancel_url": cancel_url,
            "metadata": metadata or {},
            "subscription_data": {},
        }
        if trial_days > 0:
            params["subscription_data"]["trial_period_days"] = trial_days
        if promotion_code:
            params["discounts"] = [{"promotion_code": promotion_code}]

        session = self._stripe.checkout.Session.create(**params)
        return str(session.url)

    def create_portal_session(self, *, customer_id: str, return_url: str) -> str:
        if not self._enabled or self._stripe is None:
            url = return_url
            logger.info("stripe_dev_portal", customer_id=customer_id, url=url)
            return url

        session = self._stripe.billing_portal.Session.create(
            customer=customer_id,
            return_url=return_url,
        )
        return str(session.url)

    def construct_event(self, payload: bytes, signature: str) -> Any:
        if not self._enabled or self._stripe is None:
            msg = "Stripe webhooks require STRIPE_WEBHOOK_SECRET"
            raise ValueError(msg)
        if not self._settings.stripe_webhook_secret:
            msg = "STRIPE_WEBHOOK_SECRET is not configured"
            raise ValueError(msg)
        return self._stripe.Webhook.construct_event(
            payload,
            signature,
            self._settings.stripe_webhook_secret,
        )

    def create_coupon(
        self,
        *,
        name: str,
        percent_off: int | None = None,
        amount_off_cents: int | None = None,
        currency: str = "USD",
        duration: str = "once",
        duration_in_months: int | None = None,
        max_redemptions: int | None = None,
    ) -> tuple[str, str]:
        """Create Stripe coupon + promotion code. Returns (coupon_id, promotion_code_id)."""
        if not self._enabled or self._stripe is None:
            coupon_id = f"coupon_dev_{name.lower().replace(' ', '_')}"
            promo_id = f"promo_dev_{name.lower().replace(' ', '_')}"
            logger.info("stripe_dev_create_coupon", coupon_id=coupon_id)
            return coupon_id, promo_id

        coupon_params: dict[str, Any] = {"name": name, "duration": duration}
        if percent_off is not None:
            coupon_params["percent_off"] = percent_off
        elif amount_off_cents is not None:
            coupon_params["amount_off"] = amount_off_cents
            coupon_params["currency"] = currency.lower()
        if duration == "repeating" and duration_in_months:
            coupon_params["duration_in_months"] = duration_in_months
        if max_redemptions is not None:
            coupon_params["max_redemptions"] = max_redemptions

        coupon = self._stripe.Coupon.create(**coupon_params)
        promotion = self._stripe.PromotionCode.create(coupon=str(coupon.id), active=True)
        return str(coupon.id), str(promotion.id)
