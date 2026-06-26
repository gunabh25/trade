"""SaaS billing API — plans, checkout, portal, invoices, admin."""

from __future__ import annotations

from uuid import UUID

from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends, Header, Request

from tradeflow.core.container import Container
from tradeflow.core.dependencies.auth import AdminUser, CurrentUser, DbSession
from tradeflow.core.responses import SuccessResponse, success
from tradeflow.features.billing.schemas import (
    AdminCreateCouponRequest,
    AdminUpdatePlanRequest,
    AdminUpdateSubscriptionRequest,
    CheckoutRequest,
    ValidateCouponRequest,
)
from tradeflow.features.billing.service import BillingService

router = APIRouter(prefix="/billing", tags=["Billing"])


@router.get(
    "/plans",
    response_model=SuccessResponse[list[dict[str, object]]],
    summary="List available subscription plans",
)
@inject
async def list_plans(
    request: Request,
    db: DbSession,
    billing_service: BillingService = Depends(Provide[Container.billing_service]),
) -> SuccessResponse[list[dict[str, object]]]:
    plans = await billing_service.list_plans(db)
    return success(
        [p.model_dump() for p in plans],
        request_id=request.state.request_id,
    )


@router.get(
    "/overview",
    response_model=SuccessResponse[dict[str, object]],
    summary="Current subscription, usage, and billing status",
)
@inject
async def get_billing_overview(
    request: Request,
    db: DbSession,
    user: CurrentUser,
    billing_service: BillingService = Depends(Provide[Container.billing_service]),
) -> SuccessResponse[dict[str, object]]:
    overview = await billing_service.get_billing_overview(db, user.user)
    return success(overview.model_dump(), request_id=request.state.request_id)


@router.post(
    "/checkout",
    response_model=SuccessResponse[dict[str, str]],
    summary="Create Stripe Checkout session",
)
@inject
async def create_checkout(
    body: CheckoutRequest,
    request: Request,
    db: DbSession,
    user: CurrentUser,
    billing_service: BillingService = Depends(Provide[Container.billing_service]),
) -> SuccessResponse[dict[str, str]]:
    result = await billing_service.create_checkout(db, user.user, body)
    return success(result.model_dump(), request_id=request.state.request_id)


@router.post(
    "/portal",
    response_model=SuccessResponse[dict[str, str]],
    summary="Create Stripe Customer Portal session",
)
@inject
async def create_portal(
    request: Request,
    db: DbSession,
    user: CurrentUser,
    billing_service: BillingService = Depends(Provide[Container.billing_service]),
) -> SuccessResponse[dict[str, str]]:
    result = await billing_service.create_portal(db, user.user)
    return success(result.model_dump(), request_id=request.state.request_id)


@router.post(
    "/coupons/validate",
    response_model=SuccessResponse[dict[str, object]],
    summary="Validate a coupon code",
)
@inject
async def validate_coupon(
    body: ValidateCouponRequest,
    request: Request,
    db: DbSession,
    billing_service: BillingService = Depends(Provide[Container.billing_service]),
) -> SuccessResponse[dict[str, object]]:
    coupon = await billing_service.validate_coupon(db, body.code, body.plan_code)
    return success(coupon.model_dump(), request_id=request.state.request_id)


@router.get(
    "/invoices",
    response_model=SuccessResponse[list[dict[str, object]]],
    summary="List invoice history",
)
@inject
async def list_invoices(
    request: Request,
    db: DbSession,
    user: CurrentUser,
    billing_service: BillingService = Depends(Provide[Container.billing_service]),
) -> SuccessResponse[list[dict[str, object]]]:
    invoices = await billing_service.list_invoices(db, user.id)
    return success(
        [inv.model_dump() for inv in invoices],
        request_id=request.state.request_id,
    )


@router.post(
    "/webhooks/stripe",
    include_in_schema=False,
)
@inject
async def stripe_webhook(
    request: Request,
    db: DbSession,
    stripe_signature: str = Header(alias="Stripe-Signature"),
    billing_service: BillingService = Depends(Provide[Container.billing_service]),
) -> dict[str, str]:
    payload = await request.body()
    return await billing_service.handle_webhook(db, payload, stripe_signature)


@router.get(
    "/admin/subscriptions",
    response_model=SuccessResponse[list[dict[str, object]]],
    summary="Admin: list all subscriptions",
)
@inject
async def admin_list_subscriptions(
    request: Request,
    db: DbSession,
    _admin: AdminUser,
    billing_service: BillingService = Depends(Provide[Container.billing_service]),
) -> SuccessResponse[list[dict[str, object]]]:
    rows = await billing_service.admin_list_subscriptions(db)
    return success(
        [row.model_dump() for row in rows],
        request_id=request.state.request_id,
    )


@router.patch(
    "/admin/subscriptions/{subscription_id}",
    response_model=SuccessResponse[dict[str, object]],
    summary="Admin: update subscription plan, status, or trial",
)
@inject
async def admin_update_subscription(
    subscription_id: UUID,
    body: AdminUpdateSubscriptionRequest,
    request: Request,
    db: DbSession,
    _admin: AdminUser,
    billing_service: BillingService = Depends(Provide[Container.billing_service]),
) -> SuccessResponse[dict[str, object]]:
    row = await billing_service.admin_update_subscription(db, subscription_id, body)
    return success(row.model_dump(), request_id=request.state.request_id)


@router.post(
    "/admin/coupons",
    response_model=SuccessResponse[dict[str, object]],
    summary="Admin: create coupon",
)
@inject
async def admin_create_coupon(
    body: AdminCreateCouponRequest,
    request: Request,
    db: DbSession,
    _admin: AdminUser,
    billing_service: BillingService = Depends(Provide[Container.billing_service]),
) -> SuccessResponse[dict[str, object]]:
    coupon = await billing_service.admin_create_coupon(db, body)
    return success(coupon.model_dump(), request_id=request.state.request_id)


@router.patch(
    "/admin/plans/{plan_code}",
    response_model=SuccessResponse[dict[str, object]],
    summary="Admin: update plan Stripe IDs and pricing",
)
@inject
async def admin_update_plan(
    plan_code: str,
    body: AdminUpdatePlanRequest,
    request: Request,
    db: DbSession,
    _admin: AdminUser,
    billing_service: BillingService = Depends(Provide[Container.billing_service]),
) -> SuccessResponse[dict[str, object]]:
    plan = await billing_service.admin_update_plan(db, plan_code, body)
    return success(plan.model_dump(), request_id=request.state.request_id)
