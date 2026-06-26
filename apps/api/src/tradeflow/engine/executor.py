"""Copy executor — places/modifies/cancels follower orders via broker sessions."""

from __future__ import annotations

import time
from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession

from tradeflow.core.logging import get_logger
from tradeflow.db.enums import CopyEventAction, OrderStatus
from tradeflow.db.models.trading import Order
from tradeflow.engine.order_types import to_broker_order_type
from tradeflow.engine.types import CopyDecision, CopyExecutionResult, FollowerContext, LeaderEvent
from tradeflow.integrations.brokers.manager import BrokerSessionManager
from tradeflow.integrations.brokers.types import (
    BrokerOrderSide,
    BrokerOrderStatus,
    ModifyOrderRequest,
    PlaceOrderRequest,
)

logger = get_logger(__name__)


class CopyExecutor:
    """Executes copy decisions against live broker sessions."""

    def __init__(self, session_manager: BrokerSessionManager) -> None:
        self._sessions = session_manager

    async def execute(
        self,
        db: AsyncSession,
        event: LeaderEvent,
        decision: CopyDecision,
        ctx: FollowerContext,
        *,
        mapped_follower_order_id: str | None = None,
    ) -> CopyExecutionResult:
        if decision.skip:
            return CopyExecutionResult(
                decision=decision,
                success=False,
                error=decision.skip_reason or "skipped",
            )

        start = time.perf_counter()
        try:
            if decision.action == CopyEventAction.PLACE:
                result = await self._place(db, event, decision, ctx)
            elif decision.action == CopyEventAction.MODIFY:
                result = await self._modify(event, decision, ctx, mapped_follower_order_id)
            elif decision.action == CopyEventAction.CANCEL:
                result = await self._cancel(event, decision, ctx, mapped_follower_order_id)
            elif decision.action in {CopyEventAction.FILL, CopyEventAction.PARTIAL_FILL}:
                result = CopyExecutionResult(
                    decision=decision,
                    success=True,
                    partial_fill=decision.action == CopyEventAction.PARTIAL_FILL,
                    filled_quantity=decision.quantity,
                )
            else:
                result = CopyExecutionResult(
                    decision=decision,
                    success=False,
                    error=f"unsupported_action:{decision.action.value}",
                )
        except Exception as exc:
            logger.error(
                "copy_execution_failed",
                follower_account_id=str(decision.follower_account_id),
                action=decision.action.value,
                error=str(exc),
            )
            result = CopyExecutionResult(
                decision=decision,
                success=False,
                error=str(exc),
            )

        result.latency_ms = int((time.perf_counter() - start) * 1000)
        return result

    async def _place(
        self,
        db: AsyncSession,
        event: LeaderEvent,
        decision: CopyDecision,
        ctx: FollowerContext,
    ) -> CopyExecutionResult:
        broker_order = await self._sessions.place_order(
            ctx.broker_connection_id,
            PlaceOrderRequest(
                account_id=ctx.external_account_id,
                symbol=event.symbol,
                side=BrokerOrderSide(decision.side.value),
                order_type=to_broker_order_type(decision.order_type),
                quantity=Decimal(decision.quantity),
                price=decision.price,
                stop_price=decision.stop_price,
            ),
        )

        db_order = Order(
            user_id=event.user_id,
            trading_account_id=ctx.follower_account_id,
            external_order_id=broker_order.id,
            symbol=event.symbol,
            side=decision.side,
            order_type=decision.order_type,
            quantity=decision.quantity,
            filled_quantity=int(broker_order.filled_quantity),
            price=decision.price,
            stop_price=decision.stop_price,
            status=self._map_status(broker_order.status),
        )
        db.add(db_order)
        await db.flush()

        partial = broker_order.status == BrokerOrderStatus.PARTIAL
        return CopyExecutionResult(
            decision=decision,
            success=True,
            follower_order_id=broker_order.id,
            follower_order_db_id=db_order.id,
            follower_price=broker_order.price,
            partial_fill=partial,
            filled_quantity=int(broker_order.filled_quantity),
        )

    async def _modify(
        self,
        event: LeaderEvent,
        decision: CopyDecision,
        ctx: FollowerContext,
        follower_order_id: str | None,
    ) -> CopyExecutionResult:
        if not follower_order_id:
            return CopyExecutionResult(
                decision=decision,
                success=False,
                error="missing_follower_order_id",
            )

        broker_order = await self._sessions.modify_order(
            ctx.broker_connection_id,
            follower_order_id,
            ModifyOrderRequest(
                quantity=Decimal(decision.quantity) if decision.quantity else None,
                price=decision.price,
                stop_price=decision.stop_price,
            ),
        )
        return CopyExecutionResult(
            decision=decision,
            success=True,
            follower_order_id=broker_order.id,
            follower_price=broker_order.price,
        )

    async def _cancel(
        self,
        event: LeaderEvent,
        decision: CopyDecision,
        ctx: FollowerContext,
        follower_order_id: str | None,
    ) -> CopyExecutionResult:
        if not follower_order_id:
            return CopyExecutionResult(
                decision=decision,
                success=False,
                error="missing_follower_order_id",
            )

        broker_order = await self._sessions.cancel_order(
            ctx.broker_connection_id,
            follower_order_id,
        )
        return CopyExecutionResult(
            decision=decision,
            success=True,
            follower_order_id=broker_order.id,
        )

    @staticmethod
    def _map_status(status: BrokerOrderStatus) -> OrderStatus:
        mapping = {
            BrokerOrderStatus.PENDING: OrderStatus.PENDING,
            BrokerOrderStatus.OPEN: OrderStatus.SUBMITTED,
            BrokerOrderStatus.PARTIAL: OrderStatus.PARTIAL,
            BrokerOrderStatus.FILLED: OrderStatus.FILLED,
            BrokerOrderStatus.CANCELED: OrderStatus.CANCELED,
            BrokerOrderStatus.REJECTED: OrderStatus.REJECTED,
        }
        return mapping.get(status, OrderStatus.PENDING)
