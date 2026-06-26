"""Real-time risk monitor — periodic account health checks."""

from __future__ import annotations

from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from tradeflow.core.logging import get_logger
from tradeflow.db.enums import RiskMonitorStatus
from tradeflow.db.models.risk import RiskMonitorSnapshot, RiskRule
from tradeflow.db.models.trading import TradingAccount
from tradeflow.integrations.brokers.manager import BrokerSessionManager
from tradeflow.risk.actions import RiskActionExecutor
from tradeflow.risk.alerts import RiskAlertService
from tradeflow.risk.evaluator import RiskEvaluator
from tradeflow.risk.state import RiskStateStore
from tradeflow.risk.types import AccountRiskState

logger = get_logger(__name__)


class RiskMonitor:
    """Background monitor that evaluates all enabled risk rules."""

    def __init__(
        self,
        evaluator: RiskEvaluator,
        action_executor: RiskActionExecutor,
        alert_service: RiskAlertService,
        state_store: RiskStateStore,
        session_manager: BrokerSessionManager,
    ) -> None:
        self._evaluator = evaluator
        self._actions = action_executor
        self._alerts = alert_service
        self._state = state_store
        self._sessions = session_manager

    async def monitor_account(
        self,
        db: AsyncSession,
        rule: RiskRule,
    ) -> RiskMonitorSnapshot:
        """Refresh state from broker and run all risk checks."""
        account = await db.get(TradingAccount, rule.trading_account_id)
        if account is None:
            msg = f"Account {rule.trading_account_id} not found"
            raise ValueError(msg)

        state = await self._refresh_state(db, rule, account)
        result = await self._evaluator.check_account(rule, rule.trading_account_id)

        snapshot = RiskMonitorSnapshot(
            trading_account_id=rule.trading_account_id,
            status=result.status,
            daily_pnl=state.daily_pnl,
            drawdown_usd=state.drawdown_usd,
            peak_equity=state.peak_equity,
            current_equity=state.current_equity,
            total_open_contracts=state.total_open_contracts,
            current_leverage=state.current_leverage,
            kill_switch_active=state.kill_switch_active or rule.kill_switch_active,
        )
        db.add(snapshot)

        if not result.allowed and result.violations:
            for violation in result.violations:
                breach = await self._actions.handle_breach(
                    db,
                    rule=rule,
                    account_id=rule.trading_account_id,
                    user_id=rule.user_id,
                    violation=violation,
                )
                await self._alerts.send_breach_alert(
                    db,
                    user_id=rule.user_id,
                    breach=breach,
                )

        await db.flush()
        return snapshot

    async def monitor_all(self, db: AsyncSession) -> dict[str, int]:
        """Monitor all enabled risk rules."""
        rules = await db.scalars(
            select(RiskRule).where(
                RiskRule.enabled.is_(True),
                RiskRule.deleted_at.is_(None),
            ),
        )
        checked = 0
        breached = 0

        for rule in rules.all():
            try:
                snapshot = await self.monitor_account(db, rule)
                checked += 1
                if snapshot.status in {RiskMonitorStatus.BREACHED, RiskMonitorStatus.KILL_SWITCH}:
                    breached += 1
            except Exception as exc:
                logger.error(
                    "risk_monitor_failed",
                    account_id=str(rule.trading_account_id),
                    error=str(exc),
                )

        logger.info("risk_monitor_complete", checked=checked, breached=breached)
        return {"checked": checked, "breached": breached}

    async def _refresh_state(
        self,
        db: AsyncSession,
        rule: RiskRule,
        account: TradingAccount,
    ) -> AccountRiskState:
        state = await self._state.get_state(rule.trading_account_id)

        equity = account.balance or Decimal("0")
        state.current_equity = equity
        if equity > state.peak_equity:
            state.peak_equity = equity
        state.drawdown_usd = state.peak_equity - equity

        try:
            positions = await self._sessions.fetch_positions(
                account.broker_connection_id,
                account.external_account_id,
            )
            contracts: dict[str, int] = {}
            total_notional = Decimal("0")
            for pos in positions:
                contracts[pos.symbol] = int(pos.quantity)
                total_notional += pos.quantity * pos.mark_price

            state.contracts_by_symbol = contracts
            state.total_open_contracts = sum(abs(v) for v in contracts.values())
            if equity > 0:
                state.current_leverage = total_notional / equity
        except Exception:
            pass

        state.kill_switch_active = rule.kill_switch_active
        await self._state.save_state(state)
        return state

    async def reset_daily_sessions(self, db: AsyncSession) -> int:
        """Reset daily P&L for accounts whose session reset time has passed."""
        rules = await db.scalars(
            select(RiskRule).where(
                RiskRule.enabled.is_(True),
                RiskRule.session_reset_time.isnot(None),
                RiskRule.deleted_at.is_(None),
            ),
        )
        reset_count = 0
        for rule in rules.all():
            await self._state.reset_daily(rule.trading_account_id)
            reset_count += 1

        logger.info("risk_daily_sessions_reset", count=reset_count)
        return reset_count
