"""Risk breach response actions — flatten, stop copying, lock account."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from tradeflow.core.logging import get_logger
from tradeflow.db.enums import (
    CopyFollowerStatus,
    CopyGroupStatus,
    RiskAction,
    TradingAccountStatus,
)
from tradeflow.db.models.copy_trading import CopyGroup, CopyGroupFollower
from tradeflow.db.models.risk import RiskBreach, RiskRule
from tradeflow.db.models.trading import TradingAccount
from tradeflow.integrations.brokers.manager import BrokerSessionManager
from tradeflow.integrations.brokers.types import BrokerOrderSide, BrokerOrderType, PlaceOrderRequest
from tradeflow.risk.state import RiskStateStore
from tradeflow.risk.types import RiskViolation

logger = get_logger(__name__)


class RiskActionExecutor:
    """Executes automated responses to risk breaches."""

    def __init__(
        self,
        session_manager: BrokerSessionManager,
        state_store: RiskStateStore,
    ) -> None:
        self._sessions = session_manager
        self._state = state_store

    async def handle_breach(
        self,
        db: AsyncSession,
        *,
        rule: RiskRule,
        account_id: UUID,
        user_id: UUID,
        violation: RiskViolation,
    ) -> RiskBreach:
        """Record breach and execute configured automated actions."""
        action = violation.action

        breach = RiskBreach(
            user_id=user_id,
            risk_rule_id=rule.id,
            trading_account_id=account_id,
            breach_type=violation.breach_type,
            action_taken=action,
            message=violation.message,
            current_value=violation.current_value,
            limit_value=violation.limit_value,
            symbol=violation.symbol,
        )
        db.add(breach)
        await db.flush()

        if action in {RiskAction.FLATTEN, RiskAction.STOP_COPYING, RiskAction.LOCK_ACCOUNT}:
            if rule.auto_flatten_on_breach and action == RiskAction.FLATTEN:
                await self.flatten_positions(db, account_id)

            if rule.auto_stop_copying_on_breach:
                await self.stop_copying(db, account_id)

            if action == RiskAction.LOCK_ACCOUNT:
                await self.lock_account(db, account_id)

        await self._state.publish_status(
            user_id,
            {
                "type": "risk_breach",
                "account_id": str(account_id),
                "breach_type": violation.breach_type.value,
                "message": violation.message,
                "action": action.value,
            },
        )

        logger.warning(
            "risk_breach_handled",
            account_id=str(account_id),
            breach_type=violation.breach_type.value,
            action=action.value,
        )
        return breach

    async def activate_kill_switch(
        self,
        db: AsyncSession,
        rule: RiskRule,
        *,
        user_id: UUID,
    ) -> None:
        rule.kill_switch_active = True
        await self._state.set_kill_switch(rule.trading_account_id, True)

        await db.execute(
            update(TradingAccount)
            .where(TradingAccount.id == rule.trading_account_id)
            .values(status=TradingAccountStatus.LOCKED),
        )

        if rule.auto_flatten_on_breach:
            await self.flatten_positions(db, rule.trading_account_id)

        if rule.auto_stop_copying_on_breach:
            await self.stop_copying(db, rule.trading_account_id)

        await db.flush()
        logger.warning("kill_switch_activated", account_id=str(rule.trading_account_id))

        await self._state.publish_status(
            user_id,
            {
                "type": "kill_switch",
                "account_id": str(rule.trading_account_id),
                "active": True,
            },
        )

    async def deactivate_kill_switch(
        self,
        db: AsyncSession,
        rule: RiskRule,
        *,
        user_id: UUID,
    ) -> None:
        rule.kill_switch_active = False
        await self._state.set_kill_switch(rule.trading_account_id, False)

        await db.execute(
            update(TradingAccount)
            .where(TradingAccount.id == rule.trading_account_id)
            .values(status=TradingAccountStatus.ACTIVE),
        )
        await db.flush()

        await self._state.publish_status(
            user_id,
            {
                "type": "kill_switch",
                "account_id": str(rule.trading_account_id),
                "active": False,
            },
        )

    async def flatten_positions(self, db: AsyncSession, account_id: UUID) -> int:
        """Close all open positions via market orders."""
        account = await db.get(TradingAccount, account_id)
        if account is None:
            return 0

        try:
            positions = await self._sessions.fetch_positions(
                account.broker_connection_id,
                account.external_account_id,
            )
        except Exception as exc:
            logger.error("flatten_fetch_failed", account_id=str(account_id), error=str(exc))
            return 0

        closed = 0
        for position in positions:
            if position.quantity <= 0:
                continue
            side = BrokerOrderSide.SELL if position.side.value == "long" else BrokerOrderSide.BUY
            try:
                await self._sessions.place_order(
                    account.broker_connection_id,
                    PlaceOrderRequest(
                        account_id=account.external_account_id,
                        symbol=position.symbol,
                        side=side,
                        order_type=BrokerOrderType.MARKET,
                        quantity=position.quantity,
                    ),
                )
                closed += 1
            except Exception as exc:
                logger.error(
                    "flatten_order_failed",
                    account_id=str(account_id),
                    symbol=position.symbol,
                    error=str(exc),
                )

        logger.info("positions_flattened", account_id=str(account_id), closed=closed)
        return closed

    async def stop_copying(self, db: AsyncSession, account_id: UUID) -> int:
        """Pause all copy groups where this account is a follower."""
        followers = await db.scalars(
            select(CopyGroupFollower).where(
                CopyGroupFollower.follower_account_id == account_id,
                CopyGroupFollower.deleted_at.is_(None),
            ),
        )
        stopped = 0
        for follower in followers.all():
            follower.status = CopyFollowerStatus.LOCKED
            follower.locked_at = datetime.now(tz=UTC)
            follower.lock_reason = "risk_breach"
            stopped += 1

        groups = await db.scalars(
            select(CopyGroup).where(
                CopyGroup.leader_account_id == account_id,
                CopyGroup.copying_enabled.is_(True),
                CopyGroup.deleted_at.is_(None),
            ),
        )
        for group in groups.all():
            group.copying_enabled = False
            group.status = CopyGroupStatus.PAUSED
            stopped += 1

        await db.flush()
        return stopped

    async def lock_account(self, db: AsyncSession, account_id: UUID) -> None:
        await db.execute(
            update(TradingAccount)
            .where(TradingAccount.id == account_id)
            .values(status=TradingAccountStatus.LOCKED),
        )
        await db.flush()
