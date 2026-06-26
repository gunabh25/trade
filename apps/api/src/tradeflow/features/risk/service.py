"""Risk management business logic."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from tradeflow.core.errors import ConflictError, NotFoundError
from tradeflow.core.logging import get_logger
from tradeflow.db.models.risk import RiskBreach, RiskRule
from tradeflow.db.models.trading import TradingAccount
from tradeflow.features.risk.schemas import (
    CreateRiskRuleRequest,
    RiskBreachResponse,
    RiskMonitorStatusResponse,
    RiskRuleResponse,
    UpdateRiskRuleRequest,
)
from tradeflow.risk.actions import RiskActionExecutor
from tradeflow.risk.alerts import RiskAlertService
from tradeflow.risk.evaluator import RiskEvaluator
from tradeflow.risk.monitor import RiskMonitor
from tradeflow.risk.state import RiskStateStore
from tradeflow.risk.types import ProposedOrder

logger = get_logger(__name__)


class RiskService:
    """CRUD for risk rules, kill switch, monitoring, and breach history."""

    def __init__(
        self,
        evaluator: RiskEvaluator,
        monitor: RiskMonitor,
        action_executor: RiskActionExecutor,
        alert_service: RiskAlertService,
        state_store: RiskStateStore,
    ) -> None:
        self._evaluator = evaluator
        self._monitor = monitor
        self._actions = action_executor
        self._alerts = alert_service
        self._state = state_store

    async def create_rule(
        self,
        db: AsyncSession,
        user_id: UUID,
        payload: CreateRiskRuleRequest,
    ) -> RiskRuleResponse:
        await self._get_account(db, user_id, payload.trading_account_id)

        existing = await db.scalar(
            select(RiskRule).where(
                RiskRule.trading_account_id == payload.trading_account_id,
                RiskRule.deleted_at.is_(None),
            ),
        )
        if existing:
            raise ConflictError("Risk rule already exists for this account")

        rule = RiskRule(user_id=user_id, trading_account_id=payload.trading_account_id)
        self._apply_config(rule, payload)
        db.add(rule)
        await db.flush()
        await db.refresh(rule)
        logger.info("risk_rule_created", rule_id=str(rule.id))
        return RiskRuleResponse.model_validate(rule)

    async def update_rule(
        self,
        db: AsyncSession,
        user_id: UUID,
        rule_id: UUID,
        payload: UpdateRiskRuleRequest,
    ) -> RiskRuleResponse:
        rule = await self._get_rule(db, user_id, rule_id)
        self._apply_config(rule, payload)
        await db.flush()
        await db.refresh(rule)
        return RiskRuleResponse.model_validate(rule)

    async def get_rule(
        self,
        db: AsyncSession,
        user_id: UUID,
        rule_id: UUID,
    ) -> RiskRuleResponse:
        rule = await self._get_rule(db, user_id, rule_id)
        return RiskRuleResponse.model_validate(rule)

    async def get_rule_by_account(
        self,
        db: AsyncSession,
        user_id: UUID,
        account_id: UUID,
    ) -> RiskRuleResponse | None:
        rule = await db.scalar(
            select(RiskRule).where(
                RiskRule.trading_account_id == account_id,
                RiskRule.user_id == user_id,
                RiskRule.deleted_at.is_(None),
            ),
        )
        if rule is None:
            return None
        return RiskRuleResponse.model_validate(rule)

    async def list_rules(
        self,
        db: AsyncSession,
        user_id: UUID,
    ) -> list[RiskRuleResponse]:
        rules = await db.scalars(
            select(RiskRule).where(
                RiskRule.user_id == user_id,
                RiskRule.deleted_at.is_(None),
            ),
        )
        return [RiskRuleResponse.model_validate(r) for r in rules.all()]

    async def delete_rule(
        self,
        db: AsyncSession,
        user_id: UUID,
        rule_id: UUID,
    ) -> None:
        rule = await self._get_rule(db, user_id, rule_id)
        rule.deleted_at = datetime.now(tz=UTC)

    async def activate_kill_switch(
        self,
        db: AsyncSession,
        user_id: UUID,
        rule_id: UUID,
    ) -> RiskRuleResponse:
        rule = await self._get_rule(db, user_id, rule_id)
        await self._actions.activate_kill_switch(db, rule, user_id=user_id)
        await self._alerts.send_kill_switch_alert(
            db,
            user_id=user_id,
            account_id=rule.trading_account_id,
            activated=True,
        )
        await db.refresh(rule)
        return RiskRuleResponse.model_validate(rule)

    async def deactivate_kill_switch(
        self,
        db: AsyncSession,
        user_id: UUID,
        rule_id: UUID,
    ) -> RiskRuleResponse:
        rule = await self._get_rule(db, user_id, rule_id)
        await self._actions.deactivate_kill_switch(db, rule, user_id=user_id)
        await self._alerts.send_kill_switch_alert(
            db,
            user_id=user_id,
            account_id=rule.trading_account_id,
            activated=False,
        )
        await db.refresh(rule)
        return RiskRuleResponse.model_validate(rule)

    async def flatten_account(
        self,
        db: AsyncSession,
        user_id: UUID,
        account_id: UUID,
    ) -> dict[str, int]:
        await self._get_account(db, user_id, account_id)
        closed = await self._actions.flatten_positions(db, account_id)
        return {"positions_closed": closed}

    async def check_pre_trade(
        self,
        db: AsyncSession,
        user_id: UUID,
        account_id: UUID,
        order: ProposedOrder,
    ) -> dict[str, object]:
        rule = await db.scalar(
            select(RiskRule).where(
                RiskRule.trading_account_id == account_id,
                RiskRule.user_id == user_id,
                RiskRule.deleted_at.is_(None),
            ),
        )
        if rule is None:
            return {"allowed": True, "violations": []}

        result = await self._evaluator.check_pre_trade(rule, account_id, order)
        return {
            "allowed": result.allowed,
            "status": result.status.value,
            "violations": [
                {
                    "type": v.breach_type.value,
                    "message": v.message,
                    "action": v.action.value,
                }
                for v in result.violations
            ],
        }

    async def get_monitor_status(
        self,
        db: AsyncSession,
        user_id: UUID,
        account_id: UUID,
    ) -> RiskMonitorStatusResponse:
        await self._get_account(db, user_id, account_id)
        rule = await db.scalar(
            select(RiskRule).where(
                RiskRule.trading_account_id == account_id,
                RiskRule.user_id == user_id,
                RiskRule.deleted_at.is_(None),
            ),
        )
        if rule is None:
            state = await self._state.get_state(account_id)
            return RiskMonitorStatusResponse(
                trading_account_id=account_id,
                status=state.status,
                daily_pnl=state.daily_pnl,
                drawdown_usd=state.drawdown_usd,
                peak_equity=state.peak_equity,
                current_equity=state.current_equity,
                total_open_contracts=state.total_open_contracts,
                current_leverage=state.current_leverage,
                kill_switch_active=state.kill_switch_active,
                checked_at=datetime.now(tz=UTC),
            )

        snapshot = await self._monitor.monitor_account(db, rule)
        return RiskMonitorStatusResponse(
            trading_account_id=account_id,
            status=snapshot.status,
            daily_pnl=snapshot.daily_pnl,
            drawdown_usd=snapshot.drawdown_usd,
            peak_equity=snapshot.peak_equity,
            current_equity=snapshot.current_equity,
            total_open_contracts=snapshot.total_open_contracts,
            current_leverage=snapshot.current_leverage,
            kill_switch_active=snapshot.kill_switch_active,
            checked_at=snapshot.created_at,
        )

    async def list_breaches(
        self,
        db: AsyncSession,
        user_id: UUID,
        *,
        account_id: UUID | None = None,
        limit: int = 50,
    ) -> list[RiskBreachResponse]:
        query = select(RiskBreach).where(RiskBreach.user_id == user_id)
        if account_id:
            query = query.where(RiskBreach.trading_account_id == account_id)
        query = query.order_by(RiskBreach.created_at.desc()).limit(limit)
        breaches = await db.scalars(query)
        return [RiskBreachResponse.model_validate(b) for b in breaches.all()]

    async def _get_rule(
        self,
        db: AsyncSession,
        user_id: UUID,
        rule_id: UUID,
    ) -> RiskRule:
        rule = await db.scalar(
            select(RiskRule).where(
                RiskRule.id == rule_id,
                RiskRule.user_id == user_id,
                RiskRule.deleted_at.is_(None),
            ),
        )
        if rule is None:
            raise NotFoundError("Risk rule not found")
        return rule

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
    def _apply_config(
        rule: RiskRule,
        config: CreateRiskRuleRequest | UpdateRiskRuleRequest,
    ) -> None:
        rule.name = config.name
        rule.enabled = config.enabled
        rule.daily_loss_limit_usd = config.daily_loss_limit_usd
        rule.trailing_drawdown_limit_usd = config.trailing_drawdown_limit_usd
        rule.max_position_size_usd = config.max_position_size_usd
        rule.max_contracts_per_symbol = config.max_contracts_per_symbol
        rule.max_total_contracts = config.max_total_contracts
        rule.max_leverage = config.max_leverage
        rule.allowed_symbols = config.allowed_symbols
        rule.blocked_symbols = config.blocked_symbols
        rule.trading_hours_start = config.trading_hours_start
        rule.trading_hours_end = config.trading_hours_end
        rule.trading_hours_timezone = config.trading_hours_timezone
        rule.session_reset_time = config.session_reset_time
        rule.auto_flatten_on_breach = config.auto_flatten_on_breach
        rule.auto_stop_copying_on_breach = config.auto_stop_copying_on_breach
