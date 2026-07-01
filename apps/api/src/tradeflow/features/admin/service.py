"""Admin portal business logic."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from tradeflow.core.audit import record_audit
from tradeflow.core.config import Settings
from tradeflow.core.errors import ConflictError, NotFoundError
from tradeflow.db.enums import (
    AnnouncementStatus,
    AuditAction,
    ConnectionStatus,
    RoleName,
    SubscriptionStatus,
    SupportTicketStatus,
    SystemLogLevel,
)
from tradeflow.db.models.admin_ops import Announcement, FeatureFlag, SupportTicket, SystemLogEntry
from tradeflow.db.models.audit import AuditLog
from tradeflow.db.models.billing import Plan, Subscription
from tradeflow.db.models.broker import BrokerConnection
from tradeflow.db.models.notification_platform import NotificationDelivery
from tradeflow.db.models.organization import Organization, OrganizationMember
from tradeflow.db.models.trading import TradingAccount
from tradeflow.db.models.user import Role, User, UserRole
from tradeflow.features.admin.schemas import (
    AdminAnalyticsResponse,
    AdminAuditLogResponse,
    AdminBrokerStatusResponse,
    AdminHealthResponse,
    AdminNotificationDeliveryResponse,
    AdminOrganizationResponse,
    AdminOverviewResponse,
    AdminPermissionsResponse,
    AdminSearchResponse,
    AdminSearchResult,
    AdminSubscriptionSummary,
    AdminSupportTicketResponse,
    AdminTradingAccountResponse,
    AdminUserResponse,
    AnnouncementResponse,
    BulkUserActionResponse,
    CreateAnnouncementRequest,
    CreateFeatureFlagRequest,
    CreateOrganizationRequest,
    CreateSupportTicketRequest,
    FeatureFlagResponse,
    SystemLogResponse,
    UpdateAnnouncementRequest,
    UpdateFeatureFlagRequest,
    UpdateOrganizationRequest,
    UpdateSupportTicketRequest,
)
from tradeflow.features.billing.service import BillingService
from tradeflow.features.broker.service import BrokerConnectionService
from tradeflow.features.health.service import HealthService
from tradeflow.integrations.brokers.monitor import ConnectionMonitor

ROLE_PERMISSIONS: dict[str, list[str]] = {
    RoleName.ADMIN.value: [
        "users:read",
        "users:write",
        "subscriptions:read",
        "subscriptions:write",
        "audit:read",
        "tickets:read",
        "tickets:write",
        "brokers:read",
        "flags:read",
        "flags:write",
        "announcements:read",
        "announcements:write",
        "analytics:read",
        "health:read",
        "logs:read",
        "permissions:write",
        "search:read",
        "organizations:read",
        "organizations:write",
        "trading_accounts:read",
        "notifications:read",
        "security:read",
        "metrics:read",
    ],
    RoleName.SUPPORT.value: [
        "users:read",
        "tickets:read",
        "tickets:write",
        "audit:read",
        "brokers:read",
        "search:read",
    ],
    RoleName.TRADER.value: [],
}


def _enum_label(value: object) -> str:
    """Serialize SQLAlchemy enum columns that may be returned as str or enum members."""
    if isinstance(value, str):
        return value
    enum_value = getattr(value, "value", None)
    if enum_value is not None:
        return str(enum_value)
    return str(value)


def _as_int(value: object) -> int:
    return int(value)  # type: ignore[arg-type]


class AdminService:
    """Platform administration — users, ops, support, and system controls."""

    def __init__(
        self,
        settings: Settings,
        health_service: HealthService,
        billing_service: BillingService,
        connection_monitor: ConnectionMonitor,
        broker_service: BrokerConnectionService | None = None,
    ) -> None:
        self._settings = settings
        self._health = health_service
        self._billing = billing_service
        self._monitor = connection_monitor
        self._broker = broker_service

    async def get_overview(self, db: AsyncSession) -> AdminOverviewResponse:
        total_users = int(
            await db.scalar(
                select(func.count()).select_from(User).where(User.deleted_at.is_(None)),
            )
            or 0,
        )
        active_users = int(
            await db.scalar(
                select(func.count())
                .select_from(User)
                .where(User.deleted_at.is_(None), User.is_active.is_(True)),
            )
            or 0,
        )
        total_subs = int(
            await db.scalar(
                select(func.count())
                .select_from(Subscription)
                .where(
                    Subscription.deleted_at.is_(None),
                ),
            )
            or 0,
        )
        active_subs = int(
            await db.scalar(
                select(func.count())
                .select_from(Subscription)
                .where(
                    Subscription.deleted_at.is_(None),
                    Subscription.status.in_(
                        [
                            SubscriptionStatus.ACTIVE,
                            SubscriptionStatus.TRIALING,
                        ],
                    ),
                ),
            )
            or 0,
        )
        open_tickets = int(
            await db.scalar(
                select(func.count())
                .select_from(SupportTicket)
                .where(
                    SupportTicket.deleted_at.is_(None),
                    SupportTicket.status.in_(
                        [
                            SupportTicketStatus.OPEN,
                            SupportTicketStatus.IN_PROGRESS,
                            SupportTicketStatus.WAITING,
                        ],
                    ),
                ),
            )
            or 0,
        )
        broker_total = int(
            await db.scalar(
                select(func.count())
                .select_from(BrokerConnection)
                .where(BrokerConnection.deleted_at.is_(None)),
            )
            or 0,
        )
        broker_errors = int(
            await db.scalar(
                select(func.count())
                .select_from(BrokerConnection)
                .where(
                    BrokerConnection.deleted_at.is_(None),
                    BrokerConnection.status == ConnectionStatus.ERROR,
                ),
            )
            or 0,
        )
        announcements = int(
            await db.scalar(
                select(func.count())
                .select_from(Announcement)
                .where(
                    Announcement.deleted_at.is_(None),
                    Announcement.status == AnnouncementStatus.PUBLISHED,
                ),
            )
            or 0,
        )
        flags = int(
            await db.scalar(
                select(func.count()).select_from(FeatureFlag).where(FeatureFlag.enabled.is_(True)),
            )
            or 0,
        )
        org_total = int(
            await db.scalar(
                select(func.count())
                .select_from(Organization)
                .where(Organization.deleted_at.is_(None)),
            )
            or 0,
        )
        trading_accounts = int(
            await db.scalar(
                select(func.count())
                .select_from(TradingAccount)
                .where(TradingAccount.deleted_at.is_(None)),
            )
            or 0,
        )
        return AdminOverviewResponse(
            total_users=total_users,
            active_users=active_users,
            total_subscriptions=total_subs,
            active_subscriptions=active_subs,
            open_tickets=open_tickets,
            broker_connections=broker_total,
            broker_errors=broker_errors,
            published_announcements=announcements,
            enabled_feature_flags=flags,
            total_organizations=org_total,
            total_trading_accounts=trading_accounts,
        )

    async def list_users(
        self,
        db: AsyncSession,
        *,
        q: str | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[AdminUserResponse], int]:
        query = (
            select(User)
            .options(selectinload(User.user_roles).selectinload(UserRole.role))
            .where(User.deleted_at.is_(None))
        )
        if q:
            pattern = f"%{q}%"
            query = query.where(
                or_(User.email.ilike(pattern), User.first_name.ilike(pattern)),
            )
        total = int(await db.scalar(select(func.count()).select_from(query.subquery())) or 0)
        rows = await db.scalars(
            query.order_by(User.created_at.desc()).offset((page - 1) * page_size).limit(page_size),
        )
        return [_user_response(u) for u in rows.all()], total

    async def update_user(
        self,
        db: AsyncSession,
        user_id: UUID,
        *,
        is_active: bool | None,
        first_name: str | None,
        last_name: str | None,
        admin_id: UUID,
    ) -> AdminUserResponse:
        user = await self._get_user(db, user_id)
        old = {"is_active": user.is_active, "first_name": user.first_name}
        if is_active is not None:
            user.is_active = is_active
        if first_name is not None:
            user.first_name = first_name
        if last_name is not None:
            user.last_name = last_name
        await db.flush()
        await record_audit(
            db,
            action=AuditAction.ADMIN,
            resource_type="user",
            resource_id=user_id,
            user_id=admin_id,
            old_values=old,
            new_values={"is_active": user.is_active, "first_name": user.first_name},
        )
        await db.refresh(user, attribute_names=["user_roles"])
        return _user_response(user)

    async def assign_role(
        self,
        db: AsyncSession,
        user_id: UUID,
        role_name: RoleName,
        admin_id: UUID,
    ) -> AdminUserResponse:
        user = await self._get_user(db, user_id)
        role = await db.scalar(select(Role).where(Role.name == role_name))
        if role is None:
            raise NotFoundError(f"Role '{role_name.value}' not found")
        existing = await db.scalar(
            select(UserRole).where(UserRole.user_id == user_id, UserRole.role_id == role.id),
        )
        if existing is not None:
            raise ConflictError("User already has this role")
        db.add(UserRole(user_id=user_id, role_id=role.id))
        await db.flush()
        await record_audit(
            db,
            action=AuditAction.ADMIN,
            resource_type="user_role",
            resource_id=user_id,
            user_id=admin_id,
            new_values={"role": role_name.value},
        )
        await db.refresh(user, attribute_names=["user_roles"])
        return _user_response(user)

    async def revoke_role(
        self,
        db: AsyncSession,
        user_id: UUID,
        role_name: RoleName,
        admin_id: UUID,
    ) -> AdminUserResponse:
        user = await self._get_user(db, user_id)
        role = await db.scalar(select(Role).where(Role.name == role_name))
        if role is None:
            raise NotFoundError(f"Role '{role_name.value}' not found")
        row = await db.scalar(
            select(UserRole).where(UserRole.user_id == user_id, UserRole.role_id == role.id),
        )
        if row is None:
            raise NotFoundError("User does not have this role")
        await db.delete(row)
        await db.flush()
        await record_audit(
            db,
            action=AuditAction.ADMIN,
            resource_type="user_role",
            resource_id=user_id,
            user_id=admin_id,
            old_values={"role": role_name.value},
        )
        await db.refresh(user, attribute_names=["user_roles"])
        return _user_response(user)

    async def get_permissions(self) -> AdminPermissionsResponse:
        return AdminPermissionsResponse(
            roles=[r.value for r in RoleName],
            permissions=ROLE_PERMISSIONS,
        )

    async def list_subscriptions(self, db: AsyncSession) -> list[AdminSubscriptionSummary]:
        rows = await self._billing.admin_list_subscriptions(db)
        return [
            AdminSubscriptionSummary(
                id=row.id,
                user_id=row.user_id,
                user_email=row.user_email,
                status=row.status,
                plan_code=row.plan_code,
                plan_name=row.plan_name,
                trial_ends_at=row.trial_ends_at,
                current_period_end=row.current_period_end,
            )
            for row in rows
        ]

    async def list_audit_logs(
        self,
        db: AsyncSession,
        *,
        action: str | None = None,
        page: int = 1,
        page_size: int = 50,
    ) -> tuple[list[AdminAuditLogResponse], int]:
        query = select(AuditLog).options(selectinload(AuditLog.user))
        if action:
            query = query.where(AuditLog.action == action)
        total = int(await db.scalar(select(func.count()).select_from(query.subquery())) or 0)
        rows = await db.scalars(
            query.order_by(AuditLog.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size),
        )
        items = [
            AdminAuditLogResponse(
                id=row.id,
                user_id=row.user_id,
                user_email=row.user.email if row.user else None,
                action=row.action,
                resource_type=row.resource_type,
                resource_id=row.resource_id,
                ip_address=str(row.ip_address) if row.ip_address else None,
                created_at=row.created_at,
                metadata=row.metadata_,
            )
            for row in rows.all()
        ]
        return items, total

    async def list_tickets(
        self,
        db: AsyncSession,
        *,
        status: SupportTicketStatus | None = None,
    ) -> list[AdminSupportTicketResponse]:
        query = select(SupportTicket).options(selectinload(SupportTicket.user))
        query = query.where(SupportTicket.deleted_at.is_(None))
        if status:
            query = query.where(SupportTicket.status == status)
        rows = await db.scalars(query.order_by(SupportTicket.created_at.desc()).limit(100))
        return [_ticket_response(t) for t in rows.all()]

    async def create_ticket(
        self,
        db: AsyncSession,
        request: CreateSupportTicketRequest,
        admin_id: UUID,
    ) -> AdminSupportTicketResponse:
        await self._get_user(db, request.user_id)
        ticket = SupportTicket(
            user_id=request.user_id,
            subject=request.subject,
            description=request.description,
            status=SupportTicketStatus.OPEN,
            priority=request.priority,
        )
        db.add(ticket)
        await db.flush()
        await record_audit(
            db,
            action=AuditAction.CREATE,
            resource_type="support_ticket",
            resource_id=ticket.id,
            user_id=admin_id,
        )
        await db.refresh(ticket, attribute_names=["user"])
        return _ticket_response(ticket)

    async def update_ticket(
        self,
        db: AsyncSession,
        ticket_id: UUID,
        request: UpdateSupportTicketRequest,
        admin_id: UUID,
    ) -> AdminSupportTicketResponse:
        ticket = await db.scalar(
            select(SupportTicket)
            .options(selectinload(SupportTicket.user))
            .where(SupportTicket.id == ticket_id, SupportTicket.deleted_at.is_(None)),
        )
        if ticket is None:
            raise NotFoundError("Ticket not found")
        if request.status is not None:
            ticket.status = request.status
            if request.status in {SupportTicketStatus.RESOLVED, SupportTicketStatus.CLOSED}:
                ticket.resolved_at = datetime.now(tz=UTC)
        if request.priority is not None:
            ticket.priority = request.priority
        if request.assigned_to_id is not None:
            ticket.assigned_to_id = request.assigned_to_id
        await db.flush()
        await record_audit(
            db,
            action=AuditAction.UPDATE,
            resource_type="support_ticket",
            resource_id=ticket_id,
            user_id=admin_id,
        )
        return _ticket_response(ticket)

    async def list_broker_status(self, db: AsyncSession) -> list[AdminBrokerStatusResponse]:
        rows = await db.scalars(
            select(BrokerConnection)
            .options(selectinload(BrokerConnection.user))
            .where(BrokerConnection.deleted_at.is_(None))
            .order_by(BrokerConnection.updated_at.desc())
            .limit(200),
        )
        live_health = self._monitor.get_all_health()
        results: list[AdminBrokerStatusResponse] = []
        for conn in rows.all():
            health = live_health.get(str(conn.id))
            results.append(
                AdminBrokerStatusResponse(
                    id=conn.id,
                    user_id=conn.user_id,
                    user_email=conn.user.email,
                    broker=conn.broker.value,
                    name=conn.name,
                    status=conn.status,
                    last_connected_at=conn.last_connected_at,
                    last_error=conn.last_error,
                    live_connected=health.connected if health else None,
                    live_latency_ms=health.latency_ms if health else None,
                ),
            )
        return results

    async def list_feature_flags(self, db: AsyncSession) -> list[FeatureFlagResponse]:
        rows = await db.scalars(select(FeatureFlag).order_by(FeatureFlag.key))
        return [FeatureFlagResponse.model_validate(r) for r in rows.all()]

    async def create_feature_flag(
        self,
        db: AsyncSession,
        request: CreateFeatureFlagRequest,
        admin_id: UUID,
    ) -> FeatureFlagResponse:
        existing = await db.scalar(select(FeatureFlag).where(FeatureFlag.key == request.key))
        if existing:
            raise ConflictError("Feature flag key already exists")
        flag = FeatureFlag(
            key=request.key,
            name=request.name,
            description=request.description,
            enabled=request.enabled,
            rules=request.rules,
        )
        db.add(flag)
        await db.flush()
        await record_audit(
            db,
            action=AuditAction.CREATE,
            resource_type="feature_flag",
            resource_id=flag.id,
            user_id=admin_id,
        )
        return FeatureFlagResponse.model_validate(flag)

    async def update_feature_flag(
        self,
        db: AsyncSession,
        key: str,
        request: UpdateFeatureFlagRequest,
        admin_id: UUID,
    ) -> FeatureFlagResponse:
        flag = await db.scalar(select(FeatureFlag).where(FeatureFlag.key == key))
        if flag is None:
            raise NotFoundError("Feature flag not found")
        if request.name is not None:
            flag.name = request.name
        if request.description is not None:
            flag.description = request.description
        if request.enabled is not None:
            flag.enabled = request.enabled
        if request.rules is not None:
            flag.rules = request.rules
        await db.flush()
        await record_audit(
            db,
            action=AuditAction.UPDATE,
            resource_type="feature_flag",
            resource_id=flag.id,
            user_id=admin_id,
        )
        return FeatureFlagResponse.model_validate(flag)

    async def delete_feature_flag(
        self,
        db: AsyncSession,
        key: str,
        admin_id: UUID,
    ) -> None:
        flag = await db.scalar(select(FeatureFlag).where(FeatureFlag.key == key))
        if flag is None:
            raise NotFoundError("Feature flag not found")
        await db.delete(flag)
        await db.flush()
        await record_audit(
            db,
            action=AuditAction.DELETE,
            resource_type="feature_flag",
            resource_id=flag.id,
            user_id=admin_id,
        )

    async def list_announcements(self, db: AsyncSession) -> list[AnnouncementResponse]:
        rows = await db.scalars(
            select(Announcement)
            .where(Announcement.deleted_at.is_(None))
            .order_by(Announcement.created_at.desc()),
        )
        return [AnnouncementResponse.model_validate(r) for r in rows.all()]

    async def create_announcement(
        self,
        db: AsyncSession,
        request: CreateAnnouncementRequest,
        admin_id: UUID,
    ) -> AnnouncementResponse:
        item = Announcement(
            title=request.title,
            body=request.body,
            status=request.status,
            starts_at=request.starts_at,
            ends_at=request.ends_at,
            target_roles=request.target_roles,
            created_by_id=admin_id,
        )
        db.add(item)
        await db.flush()
        await record_audit(
            db,
            action=AuditAction.CREATE,
            resource_type="announcement",
            resource_id=item.id,
            user_id=admin_id,
        )
        return AnnouncementResponse.model_validate(item)

    async def update_announcement(
        self,
        db: AsyncSession,
        announcement_id: UUID,
        request: UpdateAnnouncementRequest,
        admin_id: UUID,
    ) -> AnnouncementResponse:
        item = await db.scalar(
            select(Announcement).where(
                Announcement.id == announcement_id,
                Announcement.deleted_at.is_(None),
            ),
        )
        if item is None:
            raise NotFoundError("Announcement not found")
        for field in ("title", "body", "status", "starts_at", "ends_at", "target_roles"):
            value = getattr(request, field)
            if value is not None:
                setattr(item, field, value)
        await db.flush()
        await record_audit(
            db,
            action=AuditAction.UPDATE,
            resource_type="announcement",
            resource_id=item.id,
            user_id=admin_id,
        )
        return AnnouncementResponse.model_validate(item)

    async def delete_announcement(
        self,
        db: AsyncSession,
        announcement_id: UUID,
        admin_id: UUID,
    ) -> None:
        item = await db.scalar(select(Announcement).where(Announcement.id == announcement_id))
        if item is None or item.deleted_at is not None:
            raise NotFoundError("Announcement not found")
        item.deleted_at = datetime.now(tz=UTC)
        await db.flush()
        await record_audit(
            db,
            action=AuditAction.DELETE,
            resource_type="announcement",
            resource_id=announcement_id,
            user_id=admin_id,
        )

    async def get_analytics(self, db: AsyncSession) -> AdminAnalyticsResponse:
        subs_by_plan = await db.execute(
            select(Plan.code, Plan.name, func.count(Subscription.id))
            .join(Subscription, Subscription.plan_id == Plan.id)
            .where(Subscription.deleted_at.is_(None))
            .group_by(Plan.code, Plan.name),
        )
        tickets_by_status = await db.execute(
            select(SupportTicket.status, func.count(SupportTicket.id))
            .where(SupportTicket.deleted_at.is_(None))
            .group_by(SupportTicket.status),
        )
        connections_by_broker = await db.execute(
            select(BrokerConnection.broker, func.count(BrokerConnection.id))
            .where(BrokerConnection.deleted_at.is_(None))
            .group_by(BrokerConnection.broker),
        )
        mrr = await db.scalar(
            select(func.coalesce(func.sum(Plan.price_cents), 0))
            .select_from(Subscription)
            .join(Plan, Subscription.plan_id == Plan.id)
            .where(
                Subscription.deleted_at.is_(None),
                Subscription.status.in_(
                    [SubscriptionStatus.ACTIVE, SubscriptionStatus.TRIALING],
                ),
                Plan.price_cents > 0,
            ),
        )
        users_by_month_rows = await db.execute(
            select(
                func.to_char(func.date_trunc("month", User.created_at), "YYYY-MM").label("month"),
                func.count(User.id).label("count"),
            )
            .where(User.deleted_at.is_(None))
            .group_by(func.date_trunc("month", User.created_at))
            .order_by(func.date_trunc("month", User.created_at).desc())
            .limit(12),
        )
        users_by_month = [
            {"month": str(month), "count": _as_int(count)}
            for month, count in reversed(users_by_month_rows.all())
        ]
        return AdminAnalyticsResponse(
            users_by_month=users_by_month,
            subscriptions_by_plan=[
                {"code": str(code), "name": str(name), "count": _as_int(count)}
                for code, name, count in subs_by_plan.all()
            ],
            tickets_by_status=[
                {"status": _enum_label(status), "count": _as_int(count)}
                for status, count in tickets_by_status.all()
            ],
            connections_by_broker=[
                {"broker": _enum_label(broker), "count": _as_int(count)}
                for broker, count in connections_by_broker.all()
            ],
            mrr_cents=_as_int(mrr or 0),
        )

    async def get_system_health(self) -> AdminHealthResponse:
        from tradeflow import __version__

        readiness = await self._health.get_readiness()
        live = self._monitor.get_all_health()
        connected = sum(1 for h in live.values() if h.connected)
        celery_check = readiness.checks["celery_broker"]
        celery_payload: dict[str, object] = celery_check.model_dump()
        try:
            from tradeflow.workers.celery_app import celery_app

            inspect = celery_app.control.inspect(timeout=2.0)
            if inspect is not None:
                stats = inspect.stats() or {}
                active = inspect.active() or {}
                celery_payload["workers"] = len(stats)
                celery_payload["active_tasks"] = sum(len(tasks) for tasks in active.values())
        except Exception as exc:
            celery_payload["inspect_error"] = str(exc)
        return AdminHealthResponse(
            status=readiness.status.value,
            environment=self._settings.app_env,
            version=__version__,
            database=readiness.checks["database"].model_dump(),
            redis=readiness.checks["redis"].model_dump(),
            broker_monitor={
                "tracked_connections": len(live),
                "connected": connected,
                "disconnected": len(live) - connected,
            },
            celery=celery_payload,
        )

    async def list_system_logs(
        self,
        db: AsyncSession,
        *,
        q: str | None = None,
        level: SystemLogLevel | None = None,
        page: int = 1,
        page_size: int = 50,
    ) -> tuple[list[SystemLogResponse], int]:
        query = select(SystemLogEntry)
        if level:
            query = query.where(SystemLogEntry.level == level)
        if q:
            pattern = f"%{q}%"
            query = query.where(
                or_(SystemLogEntry.message.ilike(pattern), SystemLogEntry.source.ilike(pattern)),
            )
        total = int(await db.scalar(select(func.count()).select_from(query.subquery())) or 0)
        rows = await db.scalars(
            query.order_by(SystemLogEntry.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size),
        )
        return [SystemLogResponse.model_validate(r) for r in rows.all()], total

    async def search(self, db: AsyncSession, query: str) -> AdminSearchResponse:
        pattern = f"%{query}%"
        results: list[AdminSearchResult] = []

        users = await db.scalars(
            select(User).where(User.email.ilike(pattern), User.deleted_at.is_(None)).limit(5),
        )
        for user in users.all():
            results.append(
                AdminSearchResult(
                    type="user",
                    id=str(user.id),
                    title=user.email,
                    subtitle=user.first_name,
                ),
            )

        tickets = await db.scalars(
            select(SupportTicket)
            .where(
                SupportTicket.deleted_at.is_(None),
                SupportTicket.subject.ilike(pattern),
            )
            .limit(5),
        )
        for ticket in tickets.all():
            results.append(
                AdminSearchResult(
                    type="ticket",
                    id=str(ticket.id),
                    title=ticket.subject,
                    subtitle=ticket.status.value,
                ),
            )

        flags = await db.scalars(
            select(FeatureFlag)
            .where(
                or_(FeatureFlag.key.ilike(pattern), FeatureFlag.name.ilike(pattern)),
            )
            .limit(5),
        )
        for flag in flags.all():
            results.append(
                AdminSearchResult(type="feature_flag", id=flag.key, title=flag.name),
            )

        return AdminSearchResponse(query=query, results=results)

    async def bulk_user_action(
        self,
        db: AsyncSession,
        user_ids: list[UUID],
        action: str,
        admin_id: UUID,
    ) -> BulkUserActionResponse:
        is_active = action == "activate"
        updated = 0
        for user_id in user_ids:
            user = await db.scalar(
                select(User).where(User.id == user_id, User.deleted_at.is_(None)),
            )
            if user is None:
                continue
            user.is_active = is_active
            updated += 1
        await db.flush()
        await record_audit(
            db,
            action=AuditAction.ADMIN,
            resource_type="user_bulk",
            resource_id=admin_id,
            user_id=admin_id,
            new_values={"action": action, "count": updated},
        )
        return BulkUserActionResponse(updated=updated, user_ids=user_ids)

    async def list_organizations(
        self,
        db: AsyncSession,
        *,
        q: str | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[AdminOrganizationResponse], int]:
        query = (
            select(Organization)
            .options(selectinload(Organization.owner))
            .where(Organization.deleted_at.is_(None))
        )
        if q:
            pattern = f"%{q}%"
            query = query.where(
                or_(Organization.name.ilike(pattern), Organization.slug.ilike(pattern)),
            )
        total = int(await db.scalar(select(func.count()).select_from(query.subquery())) or 0)
        rows = await db.scalars(
            query.order_by(Organization.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size),
        )
        orgs = rows.all()
        member_counts: dict[UUID, int] = {}
        if orgs:
            counts = await db.execute(
                select(OrganizationMember.organization_id, func.count(OrganizationMember.id))
                .where(OrganizationMember.organization_id.in_([o.id for o in orgs]))
                .group_by(OrganizationMember.organization_id),
            )
            member_counts = dict(counts.all())
        return [
            AdminOrganizationResponse(
                id=org.id,
                name=org.name,
                slug=org.slug,
                plan_code=org.plan_code,
                is_active=org.is_active,
                owner_user_id=org.owner_user_id,
                owner_email=org.owner.email if org.owner else None,
                member_count=member_counts.get(org.id, 0),
                created_at=org.created_at,
            )
            for org in orgs
        ], total

    async def create_organization(
        self,
        db: AsyncSession,
        request: CreateOrganizationRequest,
        admin_id: UUID,
    ) -> AdminOrganizationResponse:
        existing = await db.scalar(
            select(Organization).where(Organization.slug == request.slug),
        )
        if existing is not None:
            raise ConflictError("Organization slug already exists")
        if request.owner_user_id is not None:
            await self._get_user(db, request.owner_user_id)
        org = Organization(
            name=request.name,
            slug=request.slug,
            plan_code=request.plan_code,
            owner_user_id=request.owner_user_id,
        )
        db.add(org)
        await db.flush()
        if request.owner_user_id is not None:
            db.add(
                OrganizationMember(
                    organization_id=org.id,
                    user_id=request.owner_user_id,
                    role="owner",
                ),
            )
            await db.flush()
        await record_audit(
            db,
            action=AuditAction.CREATE,
            resource_type="organization",
            resource_id=org.id,
            user_id=admin_id,
        )
        await db.refresh(org, attribute_names=["owner"])
        return AdminOrganizationResponse(
            id=org.id,
            name=org.name,
            slug=org.slug,
            plan_code=org.plan_code,
            is_active=org.is_active,
            owner_user_id=org.owner_user_id,
            owner_email=org.owner.email if org.owner else None,
            member_count=1 if request.owner_user_id else 0,
            created_at=org.created_at,
        )

    async def update_organization(
        self,
        db: AsyncSession,
        org_id: UUID,
        request: UpdateOrganizationRequest,
        admin_id: UUID,
    ) -> AdminOrganizationResponse:
        org = await db.scalar(
            select(Organization)
            .options(selectinload(Organization.owner))
            .where(Organization.id == org_id, Organization.deleted_at.is_(None)),
        )
        if org is None:
            raise NotFoundError("Organization not found")
        if request.name is not None:
            org.name = request.name
        if request.plan_code is not None:
            org.plan_code = request.plan_code
        if request.is_active is not None:
            org.is_active = request.is_active
        if request.owner_user_id is not None:
            await self._get_user(db, request.owner_user_id)
            org.owner_user_id = request.owner_user_id
        await db.flush()
        await record_audit(
            db,
            action=AuditAction.UPDATE,
            resource_type="organization",
            resource_id=org.id,
            user_id=admin_id,
        )
        member_count = int(
            await db.scalar(
                select(func.count())
                .select_from(OrganizationMember)
                .where(OrganizationMember.organization_id == org.id),
            )
            or 0,
        )
        return AdminOrganizationResponse(
            id=org.id,
            name=org.name,
            slug=org.slug,
            plan_code=org.plan_code,
            is_active=org.is_active,
            owner_user_id=org.owner_user_id,
            owner_email=org.owner.email if org.owner else None,
            member_count=member_count,
            created_at=org.created_at,
        )

    async def list_trading_accounts(
        self,
        db: AsyncSession,
        *,
        q: str | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[AdminTradingAccountResponse], int]:
        query = (
            select(TradingAccount)
            .options(selectinload(TradingAccount.user))
            .where(TradingAccount.deleted_at.is_(None))
        )
        if q:
            pattern = f"%{q}%"
            query = query.where(
                or_(
                    TradingAccount.name.ilike(pattern),
                    TradingAccount.external_account_id.ilike(pattern),
                ),
            )
        total = int(await db.scalar(select(func.count()).select_from(query.subquery())) or 0)
        rows = await db.scalars(
            query.order_by(TradingAccount.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size),
        )
        return [
            AdminTradingAccountResponse(
                id=row.id,
                user_id=row.user_id,
                user_email=row.user.email,
                broker_connection_id=row.broker_connection_id,
                name=row.name,
                external_account_id=row.external_account_id,
                account_type=row.account_type.value,
                account_role=row.account_role.value,
                status=row.status.value,
                currency=row.currency,
                balance=float(row.balance) if row.balance is not None else None,
                created_at=row.created_at,
            )
            for row in rows.all()
        ], total

    async def list_notification_deliveries(
        self,
        db: AsyncSession,
        *,
        status: str | None = None,
        page: int = 1,
        page_size: int = 50,
    ) -> tuple[list[AdminNotificationDeliveryResponse], int]:
        query = select(NotificationDelivery).options(
            selectinload(NotificationDelivery.user),
        )
        if status:
            query = query.where(NotificationDelivery.status == status)
        total = int(await db.scalar(select(func.count()).select_from(query.subquery())) or 0)
        rows = await db.scalars(
            query.order_by(NotificationDelivery.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size),
        )
        return [
            AdminNotificationDeliveryResponse(
                id=row.id,
                user_id=row.user_id,
                user_email=row.user.email if row.user else None,
                event_type=row.event_type,
                channel=row.channel,
                status=row.status,
                attempts=row.attempts,
                last_error=row.last_error,
                created_at=row.created_at,
            )
            for row in rows.all()
        ], total

    async def admin_disconnect_broker(
        self,
        db: AsyncSession,
        connection_id: UUID,
        admin_id: UUID,
    ) -> AdminBrokerStatusResponse:
        conn = await db.scalar(
            select(BrokerConnection)
            .options(selectinload(BrokerConnection.user))
            .where(
                BrokerConnection.id == connection_id,
                BrokerConnection.deleted_at.is_(None),
            ),
        )
        if conn is None:
            raise NotFoundError("Broker connection not found")
        if self._broker is not None:
            await self._broker.disconnect(db, conn.user_id, connection_id)
        else:
            conn.status = ConnectionStatus.DISCONNECTED
            await db.flush()
        await record_audit(
            db,
            action=AuditAction.ADMIN,
            resource_type="broker_connection",
            resource_id=connection_id,
            user_id=admin_id,
        )
        live_health = self._monitor.get_all_health().get(str(conn.id))
        return AdminBrokerStatusResponse(
            id=conn.id,
            user_id=conn.user_id,
            user_email=conn.user.email,
            broker=conn.broker.value,
            name=conn.name,
            status=conn.status,
            last_connected_at=conn.last_connected_at,
            last_error=conn.last_error,
            live_connected=live_health.connected if live_health else None,
            live_latency_ms=live_health.latency_ms if live_health else None,
        )

    async def _get_user(self, db: AsyncSession, user_id: UUID) -> User:
        user = await db.scalar(
            select(User)
            .options(selectinload(User.user_roles).selectinload(UserRole.role))
            .where(User.id == user_id, User.deleted_at.is_(None)),
        )
        if user is None:
            raise NotFoundError("User not found")
        return user


def _user_response(user: User) -> AdminUserResponse:
    return AdminUserResponse(
        id=user.id,
        email=user.email,
        first_name=user.first_name,
        last_name=user.last_name,
        is_active=user.is_active,
        roles=[ur.role.name.value for ur in user.user_roles],
        created_at=user.created_at,
        email_verified=user.email_verified_at is not None,
    )


def _ticket_response(ticket: SupportTicket) -> AdminSupportTicketResponse:
    return AdminSupportTicketResponse(
        id=ticket.id,
        user_id=ticket.user_id,
        user_email=ticket.user.email,
        assigned_to_id=ticket.assigned_to_id,
        subject=ticket.subject,
        description=ticket.description,
        status=ticket.status,
        priority=ticket.priority,
        created_at=ticket.created_at,
        updated_at=ticket.updated_at,
        resolved_at=ticket.resolved_at,
    )
