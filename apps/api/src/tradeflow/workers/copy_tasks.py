"""Celery tasks for copy engine — async processing and retry drain."""

from __future__ import annotations

import asyncio
from typing import Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from tradeflow.core.config import get_settings
from tradeflow.core.logging import configure_logging, get_logger
from tradeflow.core.security.encryption import EncryptionService
from tradeflow.db.enums import CopyEventAction, OrderSide, OrderType
from tradeflow.db.models.copy_trading import ExecutionLog
from tradeflow.engine.mapping import TradeMappingStore
from tradeflow.engine.orchestrator import CopyOrchestrator
from tradeflow.engine.recovery import ConnectionRecovery
from tradeflow.engine.retry_queue import RetryQueue
from tradeflow.engine.sync import CopySynchronizer
from tradeflow.engine.types import CopyDecision, FollowerContext, LeaderEvent, LeaderEventType
from tradeflow.integrations.brokers.manager import BrokerSessionManager
from tradeflow.integrations.brokers.monitor import ConnectionMonitor
from tradeflow.integrations.brokers.registry import BrokerAdapterRegistry
from tradeflow.workers.celery_app import celery_app

logger = get_logger(__name__)


def _run_async(coro: Any) -> Any:
    return asyncio.run(coro)


def _build_orchestrator() -> tuple[CopyOrchestrator, async_sessionmaker[AsyncSession], Any]:
    settings = get_settings()
    configure_logging(settings)

    engine = create_async_engine(str(settings.database_url), pool_pre_ping=True)
    session_factory = async_sessionmaker(engine, expire_on_commit=False)

    import redis.asyncio as aioredis

    redis = aioredis.from_url(str(settings.redis_url), decode_responses=True)
    encryption = EncryptionService(settings=settings)
    registry = BrokerAdapterRegistry()
    monitor = ConnectionMonitor()
    session_manager = BrokerSessionManager(registry, monitor, encryption)
    mapping_store = TradeMappingStore(redis)
    retry_queue = RetryQueue(redis, max_attempts=settings.copy_retry_max_attempts)
    orchestrator = CopyOrchestrator(session_manager, mapping_store, retry_queue)

    return orchestrator, session_factory, redis


@celery_app.task(name="tradeflow.workers.copy_tasks.process_leader_event")  # type: ignore[untyped-decorator]
def process_leader_event(event_payload: dict[str, Any]) -> dict[str, Any]:
    """Process a leader event asynchronously via Celery."""

    async def _process() -> dict[str, Any]:
        orchestrator, session_factory, redis = _build_orchestrator()
        try:
            event = _payload_to_leader_event(event_payload)
            async with session_factory() as db:
                results = await orchestrator.handle_leader_event(db, event)
                await db.commit()
            return {
                "processed": len(results),
                "successes": sum(1 for r in results if r.success),
            }
        finally:
            await redis.close()

    return _run_async(_process())


@celery_app.task(name="tradeflow.workers.copy_tasks.drain_retry_queue")  # type: ignore[untyped-decorator]
def drain_retry_queue() -> dict[str, int]:
    """Drain ready retry items from Redis queue."""

    async def _drain() -> dict[str, int]:
        orchestrator, session_factory, redis = _build_orchestrator()
        retry_queue = RetryQueue(redis, max_attempts=get_settings().copy_retry_max_attempts)
        processed = 0
        failed = 0

        try:
            items = await retry_queue.dequeue_ready(limit=50)
            for item in items:
                execution_log_id = UUID(item["execution_log_id"])
                payload = item["payload"]
                async with session_factory() as db:
                    log = await db.get(ExecutionLog, execution_log_id)
                    if log is None:
                        continue
                    event = await _load_event_from_payload(db, payload)
                    decision = _payload_to_decision(payload["decision"])
                    ctx = await _load_follower_context(db, decision.follower_account_id)
                    if ctx is None:
                        failed += 1
                        continue
                    result = await orchestrator.retry_execution(
                        db,
                        execution_log_id,
                        event,
                        decision,
                        ctx,
                    )
                    await db.commit()
                    if result.success:
                        processed += 1
                    else:
                        failed += 1
        finally:
            await redis.close()

        logger.info("retry_queue_drained", processed=processed, failed=failed)
        return {"processed": processed, "failed": failed}

    return _run_async(_drain())


@celery_app.task(name="tradeflow.workers.copy_tasks.recover_connections")  # type: ignore[untyped-decorator]
def recover_connections() -> dict[str, int]:
    """Reconnect broker sessions for active copy groups."""

    async def _recover() -> dict[str, int]:
        _, session_factory, redis = _build_orchestrator()
        settings = get_settings()
        encryption = EncryptionService(settings=settings)
        registry = BrokerAdapterRegistry()
        monitor = ConnectionMonitor()
        session_manager = BrokerSessionManager(registry, monitor, encryption)
        from tradeflow.notifications.dispatcher import NotificationDispatcher

        dispatcher = NotificationDispatcher(settings, redis)
        recovery = ConnectionRecovery(session_manager, notification_dispatcher=dispatcher)

        try:
            async with session_factory() as db:
                count = await recovery.recover_active_connections(db)
                await db.commit()
            return {"recovered": count}
        finally:
            await redis.aclose()

    return _run_async(_recover())


@celery_app.task(name="tradeflow.workers.copy_tasks.sync_copy_groups")  # type: ignore[untyped-decorator]
def sync_copy_groups(copy_group_id: str) -> dict[str, Any]:
    """Reconcile follower orders for a copy group."""

    async def _sync() -> dict[str, Any]:
        _, session_factory, redis = _build_orchestrator()
        settings = get_settings()
        encryption = EncryptionService(settings=settings)
        registry = BrokerAdapterRegistry()
        monitor = ConnectionMonitor()
        session_manager = BrokerSessionManager(registry, monitor, encryption)
        synchronizer = CopySynchronizer(session_manager)
        gid = UUID(copy_group_id)
        totals = {"synced": 0, "drift": 0}

        try:
            from sqlalchemy import select

            from tradeflow.db.models.copy_trading import CopyGroupFollower

            async with session_factory() as db:
                followers = await db.scalars(
                    select(CopyGroupFollower).where(
                        CopyGroupFollower.copy_group_id == gid,
                        CopyGroupFollower.deleted_at.is_(None),
                    ),
                )
                for follower in followers.all():
                    stats = await synchronizer.sync_follower_orders(
                        db,
                        copy_group_id=gid,
                        follower_account_id=follower.follower_account_id,
                    )
                    totals["synced"] += stats["synced"]
                    totals["drift"] += stats["drift"]
                await db.commit()
        finally:
            await redis.close()

        return totals

    return _run_async(_sync())


def _payload_to_leader_event(payload: dict[str, Any]) -> LeaderEvent:
    from decimal import Decimal

    return LeaderEvent(
        id=payload["id"],
        copy_group_id=UUID(payload["copy_group_id"]),
        leader_account_id=UUID(payload["leader_account_id"]),
        user_id=UUID(payload["user_id"]),
        event_type=LeaderEventType(payload["event_type"]),
        leader_order_id=payload["leader_order_id"],
        symbol=payload["symbol"],
        side=OrderSide(payload["side"]),
        order_type=OrderType(payload["order_type"]),
        quantity=payload["quantity"],
        price=Decimal(payload["price"]) if payload.get("price") else None,
        stop_price=Decimal(payload["stop_price"]) if payload.get("stop_price") else None,
        filled_quantity=payload.get("filled_quantity", 0),
    )


def _payload_to_decision(data: dict[str, Any]) -> CopyDecision:
    from decimal import Decimal

    from tradeflow.db.enums import OrderLegType

    return CopyDecision(
        follower_account_id=UUID(data["follower_account_id"]),
        follower_config_id=UUID(data["follower_config_id"]),
        action=CopyEventAction(data["action"]),
        quantity=data["quantity"],
        side=OrderSide(data["side"]),
        order_type=OrderType(data["order_type"]),
        price=Decimal(data["price"]) if data.get("price") else None,
        stop_price=Decimal(data["stop_price"]) if data.get("stop_price") else None,
        leg_type=OrderLegType(data.get("leg_type", "entry")),
    )


async def _load_event_from_payload(db: AsyncSession, payload: dict[str, Any]) -> LeaderEvent:
    from sqlalchemy import select

    from tradeflow.db.models.copy_trading import CopyGroup

    group = await db.scalar(
        select(CopyGroup).where(CopyGroup.id == UUID(payload.get("copy_group_id", ""))),
    )
    if group is None:
        msg = "Copy group not found for retry payload"
        raise ValueError(msg)

    return LeaderEvent(
        id=payload.get("event_id", ""),
        copy_group_id=group.id,
        leader_account_id=group.leader_account_id,
        user_id=group.user_id,
        event_type=LeaderEventType.ORDER_SUBMITTED,
        leader_order_id=payload.get("leader_order_id", ""),
        symbol=payload.get("symbol", ""),
        side=OrderSide.BUY,
        order_type=OrderType.MARKET,
        quantity=0,
    )


async def _load_follower_context(
    db: AsyncSession,
    follower_account_id: UUID,
) -> FollowerContext | None:
    from sqlalchemy import select

    from tradeflow.db.models.copy_trading import CopyGroupFollower
    from tradeflow.db.models.trading import TradingAccount

    follower = await db.scalar(
        select(CopyGroupFollower).where(
            CopyGroupFollower.follower_account_id == follower_account_id,
            CopyGroupFollower.deleted_at.is_(None),
        ),
    )
    account = await db.get(TradingAccount, follower_account_id)
    if follower is None or account is None:
        return None

    return FollowerContext(
        follower_account_id=follower_account_id,
        broker_connection_id=account.broker_connection_id,
        external_account_id=account.external_account_id,
        copy_mode=follower.copy_mode,
        sizing_value=follower.sizing_value,
        enabled=follower.enabled,
        status=follower.status.value,
        follower_balance=account.balance,
    )
