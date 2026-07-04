"""Copy trading business logic."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from tradeflow.core.errors import ConflictError, NotFoundError
from tradeflow.core.logging import get_logger
from tradeflow.db.enums import (
    CopyGroupStatus,
    OrderSide,
    TradingAccountRole,
    UsageMetric,
)
from tradeflow.db.models.copy_trading import CopyEvent, CopyGroup, CopyGroupFollower, ExecutionLog
from tradeflow.db.models.trading import TradingAccount
from tradeflow.engine.mapping import TradeMappingStore
from tradeflow.engine.orchestrator import CopyOrchestrator
from tradeflow.engine.retry_queue import RetryQueue
from tradeflow.engine.types import LeaderEvent, LeaderEventType
from tradeflow.features.billing.entitlements import EntitlementService
from tradeflow.features.copy_trading.schemas import (
    AddFollowerRequest,
    CopyEngineHealthResponse,
    CopyEventResponse,
    CopyGroupFollowerResponse,
    CopyGroupResponse,
    CreateCopyGroupRequest,
    ExecutionLogResponse,
    SimulateLeaderEventRequest,
)

if TYPE_CHECKING:
    from tradeflow.engine.leader_watch import LeaderWatchService

logger = get_logger(__name__)


class CopyTradingService:
    """Manages copy groups and orchestrates leader event processing."""

    def __init__(
        self,
        orchestrator: CopyOrchestrator,
        mapping_store: TradeMappingStore,
        retry_queue: RetryQueue,
        entitlements: EntitlementService,
        leader_watch: LeaderWatchService | None = None,
    ) -> None:
        self._orchestrator = orchestrator
        self._mapping = mapping_store
        self._retry = retry_queue
        self._entitlements = entitlements
        self._leader_watch = leader_watch

    async def create_group(
        self,
        db: AsyncSession,
        user_id: UUID,
        payload: CreateCopyGroupRequest,
    ) -> CopyGroupResponse:
        await self._entitlements.assert_feature(db, user_id, "copy_trading")
        await self._entitlements.assert_within_limit(db, user_id, UsageMetric.COPY_GROUPS)
        leader = await self._get_account(db, user_id, payload.leader_account_id)
        if leader.account_role != TradingAccountRole.LEADER:
            leader.account_role = TradingAccountRole.LEADER

        group = CopyGroup(
            user_id=user_id,
            leader_account_id=payload.leader_account_id,
            name=payload.name,
            mode=payload.mode,
            status=CopyGroupStatus.DRAFT,
        )
        db.add(group)
        await db.flush()
        await db.refresh(group, ["followers"])
        logger.info("copy_group_created", copy_group_id=str(group.id))
        return self._to_group_response(group)

    async def add_follower(
        self,
        db: AsyncSession,
        user_id: UUID,
        group_id: UUID,
        payload: AddFollowerRequest,
    ) -> CopyGroupFollowerResponse:
        await self._get_group(db, user_id, group_id)
        follower = await self._get_account(db, user_id, payload.follower_account_id)

        if follower.account_role == TradingAccountRole.LEADER:
            raise ConflictError("Account is already designated as a leader")

        follower.account_role = TradingAccountRole.FOLLOWER

        existing = await db.scalar(
            select(CopyGroupFollower).where(
                CopyGroupFollower.copy_group_id == group_id,
                CopyGroupFollower.follower_account_id == payload.follower_account_id,
                CopyGroupFollower.deleted_at.is_(None),
            ),
        )
        if existing:
            raise ConflictError("Follower already in copy group")

        config = CopyGroupFollower(
            copy_group_id=group_id,
            follower_account_id=payload.follower_account_id,
            copy_mode=payload.copy_mode,
            sizing_value=payload.sizing_value,
        )
        db.add(config)
        await db.flush()
        await db.refresh(config)
        return CopyGroupFollowerResponse.model_validate(config)

    async def start_copying(
        self,
        db: AsyncSession,
        user_id: UUID,
        group_id: UUID,
    ) -> CopyGroupResponse:
        group = await self._get_group(db, user_id, group_id, load_followers=True)
        if not group.followers:
            raise ConflictError("Add at least one follower before starting")

        group.status = CopyGroupStatus.ACTIVE
        group.copying_enabled = True
        await db.flush()
        await db.commit()
        await db.refresh(group, ["followers"])
        if self._leader_watch is not None:
            await self._leader_watch.recover_copy_connections()
            watching = await self._leader_watch.watch_group(group_id)
            if not watching:
                logger.warning(
                    "copy_group_leader_watch_failed",
                    copy_group_id=str(group_id),
                )
        from tradeflow.workers.copy_tasks import recover_connections

        recover_connections.delay()
        logger.info("copy_group_started", copy_group_id=str(group_id))
        return self._to_group_response(group)

    async def stop_copying(
        self,
        db: AsyncSession,
        user_id: UUID,
        group_id: UUID,
    ) -> CopyGroupResponse:
        group = await self._get_group(db, user_id, group_id, load_followers=True)
        group.copying_enabled = False
        group.status = CopyGroupStatus.PAUSED
        await db.flush()
        await db.refresh(group, ["followers"])
        if self._leader_watch is not None:
            await self._leader_watch.unwatch_group(group_id)
        return self._to_group_response(group)

    async def delete_group(
        self,
        db: AsyncSession,
        user_id: UUID,
        group_id: UUID,
    ) -> None:
        group = await self._get_group(db, user_id, group_id, load_followers=True)
        now = datetime.now(tz=UTC)
        group.copying_enabled = False
        group.status = CopyGroupStatus.STOPPED
        group.deleted_at = now
        for follower in group.followers:
            if follower.deleted_at is None:
                follower.deleted_at = now
        await db.flush()
        if self._leader_watch is not None:
            await self._leader_watch.unwatch_group(group_id)
        logger.info("copy_group_deleted", copy_group_id=str(group_id))

    async def list_groups(
        self,
        db: AsyncSession,
        user_id: UUID,
    ) -> list[CopyGroupResponse]:
        groups = await db.scalars(
            select(CopyGroup)
            .options(selectinload(CopyGroup.followers))
            .where(CopyGroup.user_id == user_id, CopyGroup.deleted_at.is_(None)),
        )
        return [self._to_group_response(g) for g in groups.all()]

    async def get_group(
        self,
        db: AsyncSession,
        user_id: UUID,
        group_id: UUID,
    ) -> CopyGroupResponse:
        group = await self._get_group(db, user_id, group_id, load_followers=True)
        return self._to_group_response(group)

    async def list_events(
        self,
        db: AsyncSession,
        user_id: UUID,
        group_id: UUID,
        *,
        limit: int = 50,
    ) -> list[CopyEventResponse]:
        await self._get_group(db, user_id, group_id)
        events = await db.scalars(
            select(CopyEvent)
            .where(CopyEvent.copy_group_id == group_id, CopyEvent.user_id == user_id)
            .order_by(CopyEvent.created_at.desc())
            .limit(limit),
        )
        return [CopyEventResponse.model_validate(e) for e in events.all()]

    async def list_execution_logs(
        self,
        db: AsyncSession,
        user_id: UUID,
        group_id: UUID,
        *,
        limit: int = 50,
    ) -> list[ExecutionLogResponse]:
        await self._get_group(db, user_id, group_id)
        logs = await db.scalars(
            select(ExecutionLog)
            .where(ExecutionLog.copy_group_id == group_id, ExecutionLog.user_id == user_id)
            .order_by(ExecutionLog.created_at.desc())
            .limit(limit),
        )
        return [ExecutionLogResponse.model_validate(log) for log in logs.all()]

    async def simulate_leader_event(
        self,
        db: AsyncSession,
        user_id: UUID,
        group_id: UUID,
        payload: SimulateLeaderEventRequest,
    ) -> list[dict[str, object]]:
        group = await self._get_group(db, user_id, group_id)
        order_id = payload.leader_order_id or str(uuid4())
        event_id = f"{group.leader_account_id}:{order_id}:{int(datetime.now(tz=UTC).timestamp())}"

        event = LeaderEvent(
            id=event_id,
            copy_group_id=group_id,
            leader_account_id=group.leader_account_id,
            user_id=user_id,
            event_type=LeaderEventType.ORDER_SUBMITTED,
            leader_order_id=order_id,
            symbol=payload.symbol,
            side=OrderSide(payload.side),
            order_type=payload.order_type,
            quantity=payload.quantity,
            price=payload.price,
            stop_price=payload.stop_price,
            timestamp=datetime.now(tz=UTC),
        )

        results = await self._orchestrator.handle_leader_event(db, event)
        return [
            {
                "follower_account_id": str(r.decision.follower_account_id),
                "success": r.success,
                "follower_order_id": r.follower_order_id,
                "error": r.error,
                "latency_ms": r.latency_ms,
                "partial_fill": r.partial_fill,
            }
            for r in results
        ]

    async def engine_health(self, db: AsyncSession, user_id: UUID) -> CopyEngineHealthResponse:
        active = await db.scalar(
            select(func.count())
            .select_from(CopyGroup)
            .where(
                CopyGroup.user_id == user_id,
                CopyGroup.status == CopyGroupStatus.ACTIVE,
                CopyGroup.copying_enabled.is_(True),
                CopyGroup.deleted_at.is_(None),
            ),
        )
        return CopyEngineHealthResponse(
            active_groups=active or 0,
            retry_queue_depth=await self._retry.queue_depth(),
            dead_letter_count=await self._retry.dead_letter_count(),
        )

    async def _get_group(
        self,
        db: AsyncSession,
        user_id: UUID,
        group_id: UUID,
        *,
        load_followers: bool = False,
    ) -> CopyGroup:
        query = select(CopyGroup).where(
            CopyGroup.id == group_id,
            CopyGroup.user_id == user_id,
            CopyGroup.deleted_at.is_(None),
        )
        if load_followers:
            query = query.options(selectinload(CopyGroup.followers))
        group = await db.scalar(query)
        if group is None:
            raise NotFoundError("Copy group not found")
        return group

    async def _get_account(
        self,
        db: AsyncSession,
        user_id: UUID,
        account_id: UUID,
    ) -> TradingAccount:
        account = await db.scalar(
            select(TradingAccount).where(
                TradingAccount.id == account_id,
                TradingAccount.user_id == user_id,
                TradingAccount.deleted_at.is_(None),
            ),
        )
        if account is None:
            raise NotFoundError("Trading account not found")
        return account

    @staticmethod
    def _to_group_response(group: CopyGroup) -> CopyGroupResponse:
        followers = [
            CopyGroupFollowerResponse.model_validate(f)
            for f in group.followers
            if f.deleted_at is None
        ]
        return CopyGroupResponse(
            id=group.id,
            name=group.name,
            leader_account_id=group.leader_account_id,
            mode=group.mode,
            status=group.status,
            copying_enabled=group.copying_enabled,
            sim_validated=group.sim_validated,
            followers=followers,
            created_at=group.created_at,
        )
