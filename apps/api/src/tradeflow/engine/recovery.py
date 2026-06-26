"""Connection recovery — reconnect broker sessions after disconnect."""

from __future__ import annotations

from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from tradeflow.core.logging import get_logger
from tradeflow.db.enums import ConnectionStatus, CopyGroupStatus
from tradeflow.db.models.broker import BrokerConnection
from tradeflow.db.models.copy_trading import CopyGroup, CopyGroupFollower
from tradeflow.db.models.trading import TradingAccount
from tradeflow.integrations.brokers.manager import BrokerSessionManager

if TYPE_CHECKING:
    from tradeflow.notifications.dispatcher import NotificationDispatcher

logger = get_logger(__name__)


class ConnectionRecovery:
    """Restores broker sessions for active copy groups on startup or disconnect."""

    def __init__(
        self,
        session_manager: BrokerSessionManager,
        notification_dispatcher: NotificationDispatcher | None = None,
    ) -> None:
        self._sessions = session_manager
        self._notifications = notification_dispatcher

    async def recover_active_connections(self, db: AsyncSession) -> int:
        """Reconnect all broker connections used by active copy groups."""
        connection_ids = await self._active_connection_ids(db)
        recovered = 0

        for connection_id in connection_ids:
            try:
                connection = await db.get(BrokerConnection, connection_id)
                if connection is None or connection.deleted_at is not None:
                    continue
                if connection.status == ConnectionStatus.CONNECTED:
                    health = self._sessions.get_health(connection_id)
                    if health and health.connected:
                        continue

                await self._sessions.connect(
                    connection_id,
                    connection.broker,
                    connection.credentials_encrypted,
                )
                connection.status = ConnectionStatus.CONNECTED
                recovered += 1
                logger.info("connection_recovered", connection_id=str(connection_id))
            except Exception as exc:
                connection = await db.get(BrokerConnection, connection_id)
                if connection is not None:
                    connection.status = ConnectionStatus.ERROR
                    connection.last_error = str(exc)
                    if self._notifications is not None:
                        await self._notifications.notify_broker_offline(
                            db,
                            user_id=connection.user_id,
                            broker=connection.broker.value,
                            connection_name=connection.name,
                            connection_id=connection.id,
                        )
                logger.error(
                    "connection_recovery_failed",
                    connection_id=str(connection_id),
                    error=str(exc),
                )

        await db.flush()
        return recovered

    async def recover_connection(self, db: AsyncSession, connection_id: UUID) -> bool:
        connection = await db.get(BrokerConnection, connection_id)
        if connection is None:
            return False

        try:
            await self._sessions.connect(
                connection_id,
                connection.broker,
                connection.credentials_encrypted,
            )
            connection.status = ConnectionStatus.CONNECTED
            await db.flush()
            return True
        except Exception as exc:
            connection.status = ConnectionStatus.ERROR
            connection.last_error = str(exc)
            await db.flush()
            logger.error(
                "connection_recovery_failed",
                connection_id=str(connection_id),
                error=str(exc),
            )
            return False

    async def _active_connection_ids(self, db: AsyncSession) -> set[UUID]:
        groups = await db.scalars(
            select(CopyGroup).where(
                CopyGroup.status == CopyGroupStatus.ACTIVE,
                CopyGroup.copying_enabled.is_(True),
                CopyGroup.deleted_at.is_(None),
            ),
        )
        group_list = groups.all()
        group_ids = [g.id for g in group_list]
        if not group_ids:
            return set()

        followers = await db.scalars(
            select(CopyGroupFollower).where(
                CopyGroupFollower.copy_group_id.in_(group_ids),
                CopyGroupFollower.enabled.is_(True),
                CopyGroupFollower.deleted_at.is_(None),
            ),
        )
        account_ids: set[UUID] = {g.leader_account_id for g in group_list}
        for follower in followers.all():
            account_ids.add(follower.follower_account_id)

        if not account_ids:
            return set()

        accounts = await db.scalars(
            select(TradingAccount).where(TradingAccount.id.in_(account_ids)),
        )
        return {a.broker_connection_id for a in accounts.all()}
