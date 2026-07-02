"""Watch leader accounts and dispatch copy-engine events."""

from __future__ import annotations

import contextlib
from dataclasses import dataclass
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from sqlalchemy.orm import selectinload

from tradeflow.core.logging import get_logger
from tradeflow.db.enums import BrokerType, ConnectionStatus, CopyGroupStatus
from tradeflow.db.models.broker import BrokerConnection
from tradeflow.db.models.copy_trading import CopyGroup
from tradeflow.db.models.trading import TradingAccount
from tradeflow.engine.leader_events import leader_event_to_payload, order_stream_to_leader_event
from tradeflow.engine.types import LeaderEvent
from tradeflow.integrations.brokers.manager import BrokerSessionManager
from tradeflow.integrations.brokers.types import StreamSubscription

if TYPE_CHECKING:
    from tradeflow.core.config import Settings
    from tradeflow.engine.orchestrator import CopyOrchestrator

logger = get_logger(__name__)


@dataclass(frozen=True)
class LeaderWatchContext:
    copy_group_id: UUID
    leader_account_id: UUID
    user_id: UUID
    broker_connection_id: UUID
    external_account_id: str


@dataclass
class _ActiveWatch:
    context: LeaderWatchContext
    subscription: StreamSubscription | None = None


class LeaderWatchService:
    """Subscribes to leader order streams and enqueues copy processing."""

    def __init__(
        self,
        session_factory: async_sessionmaker[AsyncSession],
        session_manager: BrokerSessionManager,
        settings: Settings,
        orchestrator: CopyOrchestrator | None = None,
    ) -> None:
        self._session_factory = session_factory
        self._sessions = session_manager
        self._settings = settings
        self._orchestrator = orchestrator
        self._watches: dict[UUID, _ActiveWatch] = {}

    async def start(self) -> None:
        await self.recover_copy_connections()
        async with self._session_factory() as db:
            groups = await self._load_active_groups(db)
        for group in groups:
            await self.watch_group(group.id)
        logger.info("leader_watch_started", active_groups=len(self._watches))

    async def recover_copy_connections(self) -> int:
        """Reconnect broker sessions for active copy groups in this process."""
        from tradeflow.engine.recovery import ConnectionRecovery

        recovery = ConnectionRecovery(self._sessions)
        async with self._session_factory() as db:
            count = await recovery.recover_active_connections(db)
            await db.commit()
        if count:
            logger.info("api_copy_connections_recovered", count=count)
        return count

    async def stop(self) -> None:
        for group_id in list(self._watches.keys()):
            await self.unwatch_group(group_id)
        logger.info("leader_watch_stopped")

    async def refresh(self) -> int:
        async with self._session_factory() as db:
            active_groups = await self._load_active_groups(db)
        active_ids = {group.id for group in active_groups}

        for group_id in list(self._watches.keys()):
            if group_id not in active_ids:
                await self.unwatch_group(group_id)

        started = 0
        for group in active_groups:
            if group.id not in self._watches and await self.watch_group(group.id):
                started += 1
        return started

    async def watch_group(self, copy_group_id: UUID) -> bool:
        if copy_group_id in self._watches:
            return True

        context = await self._load_watch_context(copy_group_id)
        if context is None:
            return False

        if not await self._ensure_broker_connected(context.broker_connection_id):
            logger.warning(
                "leader_watch_broker_not_connected",
                copy_group_id=str(copy_group_id),
                connection_id=str(context.broker_connection_id),
            )
            return False

        async def _handler(message: dict[str, object]) -> None:
            await self._on_stream_message(context, message)

        try:
            subscription = await self._sessions.stream_orders(
                context.broker_connection_id,
                context.external_account_id,
                _handler,
            )
        except Exception as exc:
            logger.error(
                "leader_watch_subscribe_failed",
                copy_group_id=str(copy_group_id),
                error=str(exc),
            )
            return False

        self._watches[copy_group_id] = _ActiveWatch(context=context, subscription=subscription)
        logger.info(
            "leader_watch_registered",
            copy_group_id=str(copy_group_id),
            leader_account_id=str(context.leader_account_id),
        )
        return True

    async def unwatch_group(self, copy_group_id: UUID) -> None:
        watch = self._watches.pop(copy_group_id, None)
        if watch is None:
            return
        if watch.subscription is not None:
            with contextlib.suppress(Exception):
                await watch.subscription.unsubscribe()
        logger.info("leader_watch_unregistered", copy_group_id=str(copy_group_id))

    async def _on_stream_message(
        self,
        context: LeaderWatchContext,
        message: dict[str, object],
    ) -> None:
        event = order_stream_to_leader_event(
            copy_group_id=context.copy_group_id,
            leader_account_id=context.leader_account_id,
            user_id=context.user_id,
            message=message,
        )
        if event is None:
            return
        await self._dispatch(event)

    async def _dispatch(self, event: LeaderEvent) -> None:
        # Run copy in the API process so paper/simulated broker state is shared with
        # the leader order stream. Celery workers have separate in-memory sessions.
        if self._orchestrator is not None:
            try:
                async with self._session_factory() as db:
                    await self._orchestrator.handle_leader_event(db, event)
                    await db.commit()
            except Exception as exc:
                logger.error(
                    "leader_event_inline_failed",
                    event_id=event.id,
                    copy_group_id=str(event.copy_group_id),
                    error=str(exc),
                )
            return

        from tradeflow.workers.copy_tasks import process_leader_event

        process_leader_event.delay(leader_event_to_payload(event))

    async def _load_watch_context(self, copy_group_id: UUID) -> LeaderWatchContext | None:
        async with self._session_factory() as db:
            group = await db.scalar(
                select(CopyGroup).where(
                    CopyGroup.id == copy_group_id,
                    CopyGroup.deleted_at.is_(None),
                    CopyGroup.status == CopyGroupStatus.ACTIVE,
                    CopyGroup.copying_enabled.is_(True),
                ),
            )
            if group is None:
                return None

            leader = await db.scalar(
                select(TradingAccount).where(
                    TradingAccount.id == group.leader_account_id,
                    TradingAccount.deleted_at.is_(None),
                ),
            )
            if leader is None:
                return None

            return LeaderWatchContext(
                copy_group_id=group.id,
                leader_account_id=leader.id,
                user_id=group.user_id,
                broker_connection_id=leader.broker_connection_id,
                external_account_id=leader.external_account_id,
            )

    async def _load_active_groups(self, db: AsyncSession) -> list[CopyGroup]:
        result = await db.scalars(
            select(CopyGroup)
            .options(selectinload(CopyGroup.followers))
            .where(
                CopyGroup.deleted_at.is_(None),
                CopyGroup.status == CopyGroupStatus.ACTIVE,
                CopyGroup.copying_enabled.is_(True),
            ),
        )
        return list(result.all())

    async def _ensure_broker_connected(self, connection_id: UUID) -> bool:
        if self._sessions.get_adapter(connection_id) is not None:
            return True

        async with self._session_factory() as db:
            connection = await db.scalar(
                select(BrokerConnection).where(
                    BrokerConnection.id == connection_id,
                    BrokerConnection.deleted_at.is_(None),
                ),
            )
            if connection is None:
                return False
            try:
                await self._sessions.connect(
                    connection.id,
                    BrokerType(connection.broker),
                    connection.credentials_encrypted,
                )
                connection.status = ConnectionStatus.CONNECTED
                await db.commit()
                return True
            except Exception as exc:
                connection.status = ConnectionStatus.ERROR
                connection.last_error = str(exc)
                await db.commit()
                logger.error(
                    "leader_watch_connect_failed",
                    connection_id=str(connection_id),
                    error=str(exc),
                )
                return False
