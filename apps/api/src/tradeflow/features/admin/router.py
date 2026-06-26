"""Admin portal API routes."""

from __future__ import annotations

from uuid import UUID

from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends, Query, Request

from tradeflow.core.container import Container
from tradeflow.core.dependencies.auth import AdminUser, DbSession
from tradeflow.core.responses import SuccessResponse, success
from tradeflow.db.enums import RoleName, SupportTicketStatus, SystemLogLevel
from tradeflow.features.admin.observability import AdminObservabilityService
from tradeflow.features.admin.schemas import (
    AdminRoleAssignmentRequest,
    AdminUpdateUserRequest,
    BulkUserActionRequest,
    CreateAnnouncementRequest,
    CreateFeatureFlagRequest,
    CreateOrganizationRequest,
    CreateSupportTicketRequest,
    UpdateAnnouncementRequest,
    UpdateFeatureFlagRequest,
    UpdateOrganizationRequest,
    UpdateSupportTicketRequest,
)
from tradeflow.features.admin.service import AdminService
from tradeflow.features.billing.schemas import (
    AdminCreateCouponRequest,
    AdminUpdatePlanRequest,
    AdminUpdateSubscriptionRequest,
)
from tradeflow.features.billing.service import BillingService

router = APIRouter(prefix="/admin", tags=["Admin"])


@router.get("/overview", response_model=SuccessResponse[dict[str, object]])
@inject
async def admin_overview(
    request: Request,
    db: DbSession,
    _admin: AdminUser,
    admin_service: AdminService = Depends(Provide[Container.admin_service]),
) -> SuccessResponse[dict[str, object]]:
    data = await admin_service.get_overview(db)
    return success(data.model_dump(), request_id=request.state.request_id)


@router.get("/search", response_model=SuccessResponse[dict[str, object]])
@inject
async def admin_search(
    request: Request,
    db: DbSession,
    _admin: AdminUser,
    q: str = Query(min_length=1),
    admin_service: AdminService = Depends(Provide[Container.admin_service]),
) -> SuccessResponse[dict[str, object]]:
    data = await admin_service.search(db, q)
    return success(data.model_dump(), request_id=request.state.request_id)


@router.get("/users", response_model=SuccessResponse[dict[str, object]])
@inject
async def list_users(
    request: Request,
    db: DbSession,
    _admin: AdminUser,
    q: str | None = None,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    admin_service: AdminService = Depends(Provide[Container.admin_service]),
) -> SuccessResponse[dict[str, object]]:
    items, total = await admin_service.list_users(db, q=q, page=page, page_size=page_size)
    return success(
        {
            "items": [i.model_dump() for i in items],
            "meta": {"page": page, "pageSize": page_size, "total": total},
        },
        request_id=request.state.request_id,
    )


@router.post("/users/bulk", response_model=SuccessResponse[dict[str, object]])
@inject
async def bulk_user_action(
    body: BulkUserActionRequest,
    request: Request,
    db: DbSession,
    admin: AdminUser,
    admin_service: AdminService = Depends(Provide[Container.admin_service]),
) -> SuccessResponse[dict[str, object]]:
    result = await admin_service.bulk_user_action(
        db,
        body.user_ids,
        body.action,
        admin.id,
    )
    return success(result.model_dump(), request_id=request.state.request_id)


@router.patch("/users/{user_id}", response_model=SuccessResponse[dict[str, object]])
@inject
async def update_user(
    user_id: UUID,
    body: AdminUpdateUserRequest,
    request: Request,
    db: DbSession,
    admin: AdminUser,
    admin_service: AdminService = Depends(Provide[Container.admin_service]),
) -> SuccessResponse[dict[str, object]]:
    user = await admin_service.update_user(
        db,
        user_id,
        is_active=body.is_active,
        first_name=body.first_name,
        last_name=body.last_name,
        admin_id=admin.id,
    )
    return success(user.model_dump(), request_id=request.state.request_id)


@router.post("/users/{user_id}/roles", response_model=SuccessResponse[dict[str, object]])
@inject
async def assign_role(
    user_id: UUID,
    body: AdminRoleAssignmentRequest,
    request: Request,
    db: DbSession,
    admin: AdminUser,
    admin_service: AdminService = Depends(Provide[Container.admin_service]),
) -> SuccessResponse[dict[str, object]]:
    user = await admin_service.assign_role(db, user_id, body.role, admin.id)
    return success(user.model_dump(), request_id=request.state.request_id)


@router.delete(
    "/users/{user_id}/roles/{role}",
    response_model=SuccessResponse[dict[str, object]],
)
@inject
async def revoke_role(
    user_id: UUID,
    role: RoleName,
    request: Request,
    db: DbSession,
    admin: AdminUser,
    admin_service: AdminService = Depends(Provide[Container.admin_service]),
) -> SuccessResponse[dict[str, object]]:
    user = await admin_service.revoke_role(db, user_id, role, admin.id)
    return success(user.model_dump(), request_id=request.state.request_id)


@router.get("/organizations", response_model=SuccessResponse[dict[str, object]])
@inject
async def list_organizations(
    request: Request,
    db: DbSession,
    _admin: AdminUser,
    q: str | None = None,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    admin_service: AdminService = Depends(Provide[Container.admin_service]),
) -> SuccessResponse[dict[str, object]]:
    items, total = await admin_service.list_organizations(db, q=q, page=page, page_size=page_size)
    return success(
        {
            "items": [i.model_dump() for i in items],
            "meta": {"page": page, "pageSize": page_size, "total": total},
        },
        request_id=request.state.request_id,
    )


@router.post("/organizations", response_model=SuccessResponse[dict[str, object]])
@inject
async def create_organization(
    body: CreateOrganizationRequest,
    request: Request,
    db: DbSession,
    admin: AdminUser,
    admin_service: AdminService = Depends(Provide[Container.admin_service]),
) -> SuccessResponse[dict[str, object]]:
    org = await admin_service.create_organization(db, body, admin.id)
    return success(org.model_dump(), request_id=request.state.request_id)


@router.patch("/organizations/{org_id}", response_model=SuccessResponse[dict[str, object]])
@inject
async def update_organization(
    org_id: UUID,
    body: UpdateOrganizationRequest,
    request: Request,
    db: DbSession,
    admin: AdminUser,
    admin_service: AdminService = Depends(Provide[Container.admin_service]),
) -> SuccessResponse[dict[str, object]]:
    org = await admin_service.update_organization(db, org_id, body, admin.id)
    return success(org.model_dump(), request_id=request.state.request_id)


@router.get("/trading-accounts", response_model=SuccessResponse[dict[str, object]])
@inject
async def list_trading_accounts(
    request: Request,
    db: DbSession,
    _admin: AdminUser,
    q: str | None = None,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    admin_service: AdminService = Depends(Provide[Container.admin_service]),
) -> SuccessResponse[dict[str, object]]:
    items, total = await admin_service.list_trading_accounts(
        db,
        q=q,
        page=page,
        page_size=page_size,
    )
    return success(
        {
            "items": [i.model_dump() for i in items],
            "meta": {"page": page, "pageSize": page_size, "total": total},
        },
        request_id=request.state.request_id,
    )


@router.get("/notifications/deliveries", response_model=SuccessResponse[dict[str, object]])
@inject
async def list_notification_deliveries(
    request: Request,
    db: DbSession,
    _admin: AdminUser,
    status: str | None = None,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=100),
    admin_service: AdminService = Depends(Provide[Container.admin_service]),
) -> SuccessResponse[dict[str, object]]:
    items, total = await admin_service.list_notification_deliveries(
        db,
        status=status,
        page=page,
        page_size=page_size,
    )
    return success(
        {
            "items": [i.model_dump() for i in items],
            "meta": {"page": page, "pageSize": page_size, "total": total},
        },
        request_id=request.state.request_id,
    )


@router.get("/permissions", response_model=SuccessResponse[dict[str, object]])
@inject
async def get_permissions(
    request: Request,
    _admin: AdminUser,
    admin_service: AdminService = Depends(Provide[Container.admin_service]),
) -> SuccessResponse[dict[str, object]]:
    data = await admin_service.get_permissions()
    return success(data.model_dump(), request_id=request.state.request_id)


@router.get("/subscriptions", response_model=SuccessResponse[list[dict[str, object]]])
@inject
async def list_subscriptions(
    request: Request,
    db: DbSession,
    _admin: AdminUser,
    admin_service: AdminService = Depends(Provide[Container.admin_service]),
) -> SuccessResponse[list[dict[str, object]]]:
    items = await admin_service.list_subscriptions(db)
    return success([i.model_dump() for i in items], request_id=request.state.request_id)


@router.patch(
    "/subscriptions/{subscription_id}",
    response_model=SuccessResponse[dict[str, object]],
)
@inject
async def update_subscription(
    subscription_id: UUID,
    body: AdminUpdateSubscriptionRequest,
    request: Request,
    db: DbSession,
    _admin: AdminUser,
    billing_service: BillingService = Depends(Provide[Container.billing_service]),
) -> SuccessResponse[dict[str, object]]:
    row = await billing_service.admin_update_subscription(db, subscription_id, body)
    return success(row.model_dump(), request_id=request.state.request_id)


@router.post("/coupons", response_model=SuccessResponse[dict[str, object]])
@inject
async def create_coupon(
    body: AdminCreateCouponRequest,
    request: Request,
    db: DbSession,
    _admin: AdminUser,
    billing_service: BillingService = Depends(Provide[Container.billing_service]),
) -> SuccessResponse[dict[str, object]]:
    coupon = await billing_service.admin_create_coupon(db, body)
    return success(coupon.model_dump(), request_id=request.state.request_id)


@router.get("/coupons", response_model=SuccessResponse[list[dict[str, object]]])
@inject
async def list_coupons(
    request: Request,
    db: DbSession,
    _admin: AdminUser,
    billing_service: BillingService = Depends(Provide[Container.billing_service]),
) -> SuccessResponse[list[dict[str, object]]]:
    coupons = await billing_service.admin_list_coupons(db)
    return success(
        [coupon.model_dump() for coupon in coupons],
        request_id=request.state.request_id,
    )


@router.get("/billing-events", response_model=SuccessResponse[list[dict[str, object]]])
@inject
async def list_billing_events(
    request: Request,
    db: DbSession,
    _admin: AdminUser,
    billing_service: BillingService = Depends(Provide[Container.billing_service]),
) -> SuccessResponse[list[dict[str, object]]]:
    events = await billing_service.admin_list_billing_events(db)
    return success(
        [event.model_dump() for event in events],
        request_id=request.state.request_id,
    )


@router.get("/invoices/failed", response_model=SuccessResponse[list[dict[str, object]]])
@inject
async def list_failed_invoices(
    request: Request,
    db: DbSession,
    _admin: AdminUser,
    billing_service: BillingService = Depends(Provide[Container.billing_service]),
) -> SuccessResponse[list[dict[str, object]]]:
    invoices = await billing_service.admin_list_failed_invoices(db)
    return success(
        [invoice.model_dump() for invoice in invoices],
        request_id=request.state.request_id,
    )


@router.patch("/plans/{plan_code}", response_model=SuccessResponse[dict[str, object]])
@inject
async def update_plan(
    plan_code: str,
    body: AdminUpdatePlanRequest,
    request: Request,
    db: DbSession,
    _admin: AdminUser,
    billing_service: BillingService = Depends(Provide[Container.billing_service]),
) -> SuccessResponse[dict[str, object]]:
    plan = await billing_service.admin_update_plan(db, plan_code, body)
    return success(plan.model_dump(), request_id=request.state.request_id)


@router.get("/audit-logs", response_model=SuccessResponse[dict[str, object]])
@inject
async def list_audit_logs(
    request: Request,
    db: DbSession,
    _admin: AdminUser,
    action: str | None = None,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=100),
    admin_service: AdminService = Depends(Provide[Container.admin_service]),
) -> SuccessResponse[dict[str, object]]:
    items, total = await admin_service.list_audit_logs(
        db,
        action=action,
        page=page,
        page_size=page_size,
    )
    return success(
        {
            "items": [i.model_dump() for i in items],
            "meta": {"page": page, "pageSize": page_size, "total": total},
        },
        request_id=request.state.request_id,
    )


@router.get("/support-tickets", response_model=SuccessResponse[list[dict[str, object]]])
@inject
async def list_support_tickets(
    request: Request,
    db: DbSession,
    _admin: AdminUser,
    status: SupportTicketStatus | None = None,
    admin_service: AdminService = Depends(Provide[Container.admin_service]),
) -> SuccessResponse[list[dict[str, object]]]:
    items = await admin_service.list_tickets(db, status=status)
    return success([i.model_dump() for i in items], request_id=request.state.request_id)


@router.post("/support-tickets", response_model=SuccessResponse[dict[str, object]])
@inject
async def create_support_ticket(
    body: CreateSupportTicketRequest,
    request: Request,
    db: DbSession,
    admin: AdminUser,
    admin_service: AdminService = Depends(Provide[Container.admin_service]),
) -> SuccessResponse[dict[str, object]]:
    ticket = await admin_service.create_ticket(db, body, admin.id)
    return success(ticket.model_dump(), request_id=request.state.request_id)


@router.patch(
    "/support-tickets/{ticket_id}",
    response_model=SuccessResponse[dict[str, object]],
)
@inject
async def update_support_ticket(
    ticket_id: UUID,
    body: UpdateSupportTicketRequest,
    request: Request,
    db: DbSession,
    admin: AdminUser,
    admin_service: AdminService = Depends(Provide[Container.admin_service]),
) -> SuccessResponse[dict[str, object]]:
    ticket = await admin_service.update_ticket(db, ticket_id, body, admin.id)
    return success(ticket.model_dump(), request_id=request.state.request_id)


@router.get("/brokers/status", response_model=SuccessResponse[list[dict[str, object]]])
@inject
async def broker_status(
    request: Request,
    db: DbSession,
    _admin: AdminUser,
    admin_service: AdminService = Depends(Provide[Container.admin_service]),
) -> SuccessResponse[list[dict[str, object]]]:
    items = await admin_service.list_broker_status(db)
    return success([i.model_dump() for i in items], request_id=request.state.request_id)


@router.post(
    "/brokers/{connection_id}/disconnect",
    response_model=SuccessResponse[dict[str, object]],
)
@inject
async def admin_disconnect_broker(
    connection_id: UUID,
    request: Request,
    db: DbSession,
    admin: AdminUser,
    admin_service: AdminService = Depends(Provide[Container.admin_service]),
) -> SuccessResponse[dict[str, object]]:
    item = await admin_service.admin_disconnect_broker(db, connection_id, admin.id)
    return success(item.model_dump(), request_id=request.state.request_id)


@router.get("/feature-flags", response_model=SuccessResponse[list[dict[str, object]]])
@inject
async def list_feature_flags(
    request: Request,
    db: DbSession,
    _admin: AdminUser,
    admin_service: AdminService = Depends(Provide[Container.admin_service]),
) -> SuccessResponse[list[dict[str, object]]]:
    items = await admin_service.list_feature_flags(db)
    return success([i.model_dump() for i in items], request_id=request.state.request_id)


@router.post("/feature-flags", response_model=SuccessResponse[dict[str, object]])
@inject
async def create_feature_flag(
    body: CreateFeatureFlagRequest,
    request: Request,
    db: DbSession,
    admin: AdminUser,
    admin_service: AdminService = Depends(Provide[Container.admin_service]),
) -> SuccessResponse[dict[str, object]]:
    flag = await admin_service.create_feature_flag(db, body, admin.id)
    return success(flag.model_dump(), request_id=request.state.request_id)


@router.patch("/feature-flags/{key}", response_model=SuccessResponse[dict[str, object]])
@inject
async def update_feature_flag(
    key: str,
    body: UpdateFeatureFlagRequest,
    request: Request,
    db: DbSession,
    admin: AdminUser,
    admin_service: AdminService = Depends(Provide[Container.admin_service]),
) -> SuccessResponse[dict[str, object]]:
    flag = await admin_service.update_feature_flag(db, key, body, admin.id)
    return success(flag.model_dump(), request_id=request.state.request_id)


@router.delete("/feature-flags/{key}", response_model=SuccessResponse[dict[str, str]])
@inject
async def delete_feature_flag(
    key: str,
    request: Request,
    db: DbSession,
    admin: AdminUser,
    admin_service: AdminService = Depends(Provide[Container.admin_service]),
) -> SuccessResponse[dict[str, str]]:
    await admin_service.delete_feature_flag(db, key, admin.id)
    return success({"deleted": key}, request_id=request.state.request_id)


@router.get("/announcements", response_model=SuccessResponse[list[dict[str, object]]])
@inject
async def list_announcements(
    request: Request,
    db: DbSession,
    _admin: AdminUser,
    admin_service: AdminService = Depends(Provide[Container.admin_service]),
) -> SuccessResponse[list[dict[str, object]]]:
    items = await admin_service.list_announcements(db)
    return success([i.model_dump() for i in items], request_id=request.state.request_id)


@router.post("/announcements", response_model=SuccessResponse[dict[str, object]])
@inject
async def create_announcement(
    body: CreateAnnouncementRequest,
    request: Request,
    db: DbSession,
    admin: AdminUser,
    admin_service: AdminService = Depends(Provide[Container.admin_service]),
) -> SuccessResponse[dict[str, object]]:
    item = await admin_service.create_announcement(db, body, admin.id)
    return success(item.model_dump(), request_id=request.state.request_id)


@router.patch(
    "/announcements/{announcement_id}",
    response_model=SuccessResponse[dict[str, object]],
)
@inject
async def update_announcement(
    announcement_id: UUID,
    body: UpdateAnnouncementRequest,
    request: Request,
    db: DbSession,
    admin: AdminUser,
    admin_service: AdminService = Depends(Provide[Container.admin_service]),
) -> SuccessResponse[dict[str, object]]:
    item = await admin_service.update_announcement(db, announcement_id, body, admin.id)
    return success(item.model_dump(), request_id=request.state.request_id)


@router.delete(
    "/announcements/{announcement_id}",
    response_model=SuccessResponse[dict[str, str]],
)
@inject
async def delete_announcement(
    announcement_id: UUID,
    request: Request,
    db: DbSession,
    admin: AdminUser,
    admin_service: AdminService = Depends(Provide[Container.admin_service]),
) -> SuccessResponse[dict[str, str]]:
    await admin_service.delete_announcement(db, announcement_id, admin.id)
    return success({"deleted": str(announcement_id)}, request_id=request.state.request_id)


@router.get("/analytics", response_model=SuccessResponse[dict[str, object]])
@inject
async def admin_analytics(
    request: Request,
    db: DbSession,
    _admin: AdminUser,
    admin_service: AdminService = Depends(Provide[Container.admin_service]),
) -> SuccessResponse[dict[str, object]]:
    data = await admin_service.get_analytics(db)
    return success(data.model_dump(), request_id=request.state.request_id)


@router.get("/metrics", response_model=SuccessResponse[dict[str, object]])
@inject
async def admin_metrics(
    request: Request,
    db: DbSession,
    _admin: AdminUser,
    observability: AdminObservabilityService = Depends(
        Provide[Container.admin_observability_service],
    ),
) -> SuccessResponse[dict[str, object]]:
    data = await observability.get_platform_metrics(db)
    return success(data, request_id=request.state.request_id)


@router.get("/security/events", response_model=SuccessResponse[dict[str, object]])
@inject
async def list_security_events(
    request: Request,
    db: DbSession,
    _admin: AdminUser,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=100),
    observability: AdminObservabilityService = Depends(
        Provide[Container.admin_observability_service],
    ),
) -> SuccessResponse[dict[str, object]]:
    items, total = await observability.list_security_events(db, page=page, page_size=page_size)
    return success(
        {
            "items": items,
            "meta": {"page": page, "pageSize": page_size, "total": total},
        },
        request_id=request.state.request_id,
    )


@router.get("/security/failed-logins", response_model=SuccessResponse[list[dict[str, object]]])
@inject
async def list_failed_logins(
    request: Request,
    _admin: AdminUser,
    observability: AdminObservabilityService = Depends(
        Provide[Container.admin_observability_service],
    ),
) -> SuccessResponse[list[dict[str, object]]]:
    items = await observability.list_failed_logins()
    return success(items, request_id=request.state.request_id)


@router.get("/health", response_model=SuccessResponse[dict[str, object]])
@inject
async def admin_health(
    request: Request,
    _admin: AdminUser,
    admin_service: AdminService = Depends(Provide[Container.admin_service]),
) -> SuccessResponse[dict[str, object]]:
    data = await admin_service.get_system_health()
    return success(data.model_dump(), request_id=request.state.request_id)


@router.get("/logs", response_model=SuccessResponse[dict[str, object]])
@inject
async def list_logs(
    request: Request,
    db: DbSession,
    _admin: AdminUser,
    q: str | None = None,
    level: SystemLogLevel | None = None,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=100),
    admin_service: AdminService = Depends(Provide[Container.admin_service]),
) -> SuccessResponse[dict[str, object]]:
    items, total = await admin_service.list_system_logs(
        db,
        q=q,
        level=level,
        page=page,
        page_size=page_size,
    )
    return success(
        {
            "items": [i.model_dump() for i in items],
            "meta": {"page": page, "pageSize": page_size, "total": total},
        },
        request_id=request.state.request_id,
    )
