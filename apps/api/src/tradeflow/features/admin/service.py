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
from tradeflow.db.models.user import Role, User, UserRole
from tradeflow.features.admin.schemas import (
    AdminAnalyticsResponse,
    AdminAuditLogResponse,
    AdminBrokerStatusResponse,
    AdminHealthResponse,
    AdminOverviewResponse,
    AdminPermissionsResponse,
    AdminSearchResponse,
    AdminSearchResult,
    AdminSubscriptionSummary,
    AdminSupportTicketResponse,
    AdminUserResponse,
    AnnouncementResponse,
    CreateAnnouncementRequest,
    CreateFeatureFlagRequest,
    CreateSupportTicketRequest,
    FeatureFlagResponse,
    SystemLogResponse,
    UpdateAnnouncementRequest,
    UpdateFeatureFlagRequest,
    UpdateSupportTicketRequest,
)
from tradeflow.features.billing.service import BillingService
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


class AdminService:
    """Platform administration — users, ops, support, and system controls."""

    def __init__(
        self,
        settings: Settings,
        health_service: HealthService,
        billing_service: BillingService,
        connection_monitor: ConnectionMonitor,
    ) -> None:
        self._settings = settings
        self._health = health_service
        self._billing = billing_service
        self._monitor = connection_monitor

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
        return AdminAnalyticsResponse(
            users_by_month=[],
            subscriptions_by_plan=[
                {"code": code, "name": name, "count": count}
                for code, name, count in subs_by_plan.all()
            ],
            tickets_by_status=[
                {"status": status.value, "count": count}
                for status, count in tickets_by_status.all()
            ],
            connections_by_broker=[
                {"broker": broker.value, "count": count}
                for broker, count in connections_by_broker.all()
            ],
            mrr_cents=int(mrr or 0),
        )

    async def get_system_health(self) -> AdminHealthResponse:
        from tradeflow import __version__

        readiness = await self._health.get_readiness()
        live = self._monitor.get_all_health()
        connected = sum(1 for h in live.values() if h.connected)
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
            celery={"status": "unknown", "note": "Configure Celery ping for live status"},
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
