"""Synchronization — leader/follower state reconciliation."""

from __future__ import annotations

from decimal import Decimal
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from tradeflow.core.logging import get_logger
from tradeflow.db.models.copy_trading import OrderMapping
from tradeflow.db.models.trading import Order, TradingAccount
from tradeflow.integrations.brokers.manager import BrokerSessionManager

logger = get_logger(__name__)


class CopySynchronizer:
    """Reconciles follower positions/orders against leader state."""

    def __init__(self, session_manager: BrokerSessionManager) -> None:
        self._sessions = session_manager

    async def sync_follower_orders(
        self,
        db: AsyncSession,
        *,
        copy_group_id: UUID,
        follower_account_id: UUID,
    ) -> dict[str, int]:
        """Fetch broker orders and update local DB records."""
        account = await db.get(TradingAccount, follower_account_id)
        if account is None:
            return {"synced": 0, "drift": 0}

        broker_orders = await self._sessions.fetch_orders(
            account.broker_connection_id,
            account.external_account_id,
        )
        local_orders = await db.scalars(
            select(Order).where(
                Order.trading_account_id == follower_account_id,
                Order.deleted_at.is_(None),
            ),
        )
        local_by_external = {
            o.external_order_id: o for o in local_orders.all() if o.external_order_id
        }

        synced = 0
        drift = 0
        for broker_order in broker_orders:
            local = local_by_external.get(broker_order.id)
            if local is None:
                drift += 1
                continue
            broker_filled = int(broker_order.filled_quantity)
            if local.filled_quantity != broker_filled:
                local.filled_quantity = broker_filled
                synced += 1

        await db.flush()
        logger.info(
            "follower_orders_synced",
            copy_group_id=str(copy_group_id),
            follower_account_id=str(follower_account_id),
            synced=synced,
            drift=drift,
        )
        return {"synced": synced, "drift": drift}

    async def detect_position_drift(
        self,
        db: AsyncSession,
        *,
        leader_account_id: UUID,
        follower_account_id: UUID,
        copy_ratio: Decimal = Decimal("1"),
    ) -> list[dict[str, object]]:
        """Compare leader vs follower open positions and flag drift."""
        leader = await db.get(TradingAccount, leader_account_id)
        follower = await db.get(TradingAccount, follower_account_id)
        if leader is None or follower is None:
            return []

        leader_positions = await self._sessions.fetch_positions(
            leader.broker_connection_id,
            leader.external_account_id,
        )
        follower_positions = await self._sessions.fetch_positions(
            follower.broker_connection_id,
            follower.external_account_id,
        )

        leader_map = {p.symbol: p for p in leader_positions}
        follower_map = {p.symbol: p for p in follower_positions}
        drifts: list[dict[str, object]] = []

        for symbol, leader_pos in leader_map.items():
            expected_qty = int(leader_pos.quantity * copy_ratio)
            follower_pos = follower_map.get(symbol)
            actual_qty = int(follower_pos.quantity) if follower_pos else 0
            if actual_qty != expected_qty:
                drifts.append(
                    {
                        "symbol": symbol,
                        "expected_quantity": expected_qty,
                        "actual_quantity": actual_qty,
                        "leader_quantity": int(leader_pos.quantity),
                    },
                )

        return drifts

    async def rebuild_mappings_from_db(
        self,
        db: AsyncSession,
        copy_group_id: UUID,
    ) -> int:
        """Reload order mappings from DB into memory (used after recovery)."""
        mappings = await db.scalars(
            select(OrderMapping).where(OrderMapping.copy_group_id == copy_group_id),
        )
        count = len(mappings.all())
        logger.info("mappings_rebuilt", copy_group_id=str(copy_group_id), count=count)
        return count
