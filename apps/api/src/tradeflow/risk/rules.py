"""Individual risk rule evaluators — Open/Closed via strategy pattern."""

from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime, time
from decimal import Decimal
from zoneinfo import ZoneInfo

from tradeflow.db.enums import RiskAction, RiskBreachType
from tradeflow.db.models.risk import RiskRule
from tradeflow.risk.types import AccountRiskState, ProposedOrder, RiskViolation


class RiskRuleEvaluator(ABC):
    """Single-responsibility rule checker."""

    @abstractmethod
    def evaluate(
        self,
        rule: RiskRule,
        state: AccountRiskState,
        order: ProposedOrder | None,
    ) -> RiskViolation | None: ...


class KillSwitchRule(RiskRuleEvaluator):
    def evaluate(
        self,
        rule: RiskRule,
        state: AccountRiskState,
        order: ProposedOrder | None,
    ) -> RiskViolation | None:
        if rule.kill_switch_active or state.kill_switch_active:
            return RiskViolation(
                breach_type=RiskBreachType.KILL_SWITCH,
                message="Kill switch is active — all trading blocked",
                action=RiskAction.BLOCK,
            )
        return None


class DailyLossRule(RiskRuleEvaluator):
    def evaluate(
        self,
        rule: RiskRule,
        state: AccountRiskState,
        order: ProposedOrder | None,
    ) -> RiskViolation | None:
        if rule.daily_loss_limit_usd is None:
            return None
        if state.daily_pnl <= -rule.daily_loss_limit_usd:
            return RiskViolation(
                breach_type=RiskBreachType.DAILY_LOSS,
                message=f"Daily loss limit breached: ${abs(state.daily_pnl)}",
                current_value=abs(state.daily_pnl),
                limit_value=rule.daily_loss_limit_usd,
                action=RiskAction.STOP_COPYING,
            )
        return None


class MaxDrawdownRule(RiskRuleEvaluator):
    def evaluate(
        self,
        rule: RiskRule,
        state: AccountRiskState,
        order: ProposedOrder | None,
    ) -> RiskViolation | None:
        if rule.trailing_drawdown_limit_usd is None:
            return None
        if state.drawdown_usd >= rule.trailing_drawdown_limit_usd:
            return RiskViolation(
                breach_type=RiskBreachType.MAX_DRAWDOWN,
                message=f"Max drawdown breached: ${state.drawdown_usd}",
                current_value=state.drawdown_usd,
                limit_value=rule.trailing_drawdown_limit_usd,
                action=RiskAction.FLATTEN,
            )
        return None


class MaxPositionSizeRule(RiskRuleEvaluator):
    def evaluate(
        self,
        rule: RiskRule,
        state: AccountRiskState,
        order: ProposedOrder | None,
    ) -> RiskViolation | None:
        if rule.max_position_size_usd is None or order is None:
            return None
        notional = order.notional_usd or Decimal(order.quantity)
        existing = state.contracts_by_symbol.get(order.symbol, 0)
        if notional > rule.max_position_size_usd:
            return RiskViolation(
                breach_type=RiskBreachType.MAX_POSITION_SIZE,
                message=f"Position size ${notional} exceeds limit ${rule.max_position_size_usd}",
                current_value=notional,
                limit_value=rule.max_position_size_usd,
                symbol=order.symbol,
                action=RiskAction.BLOCK,
            )
        if existing + order.quantity > 0 and notional > rule.max_position_size_usd:
            return RiskViolation(
                breach_type=RiskBreachType.MAX_POSITION_SIZE,
                message="Combined position would exceed size limit",
                symbol=order.symbol,
                action=RiskAction.BLOCK,
            )
        return None


class MaxContractsRule(RiskRuleEvaluator):
    def evaluate(
        self,
        rule: RiskRule,
        state: AccountRiskState,
        order: ProposedOrder | None,
    ) -> RiskViolation | None:
        if order is None:
            return None

        if rule.max_contracts_per_symbol is not None:
            current = abs(state.contracts_by_symbol.get(order.symbol, 0))
            if current + order.quantity > rule.max_contracts_per_symbol:
                return RiskViolation(
                    breach_type=RiskBreachType.MAX_CONTRACTS_PER_SYMBOL,
                    message=(
                        f"Symbol {order.symbol} contracts {current + order.quantity} "
                        f"exceeds limit {rule.max_contracts_per_symbol}"
                    ),
                    current_value=Decimal(current + order.quantity),
                    limit_value=Decimal(rule.max_contracts_per_symbol),
                    symbol=order.symbol,
                    action=RiskAction.BLOCK,
                )

        if rule.max_total_contracts is not None:
            new_total = state.total_open_contracts + order.quantity
            if new_total > rule.max_total_contracts:
                return RiskViolation(
                    breach_type=RiskBreachType.MAX_CONTRACTS,
                    message=f"Total contracts {new_total} exceeds limit {rule.max_total_contracts}",
                    current_value=Decimal(new_total),
                    limit_value=Decimal(rule.max_total_contracts),
                    action=RiskAction.BLOCK,
                )
        return None


class TradingHoursRule(RiskRuleEvaluator):
    def evaluate(
        self,
        rule: RiskRule,
        state: AccountRiskState,
        order: ProposedOrder | None,
    ) -> RiskViolation | None:
        if rule.trading_hours_start is None or rule.trading_hours_end is None:
            return None

        tz_name = rule.trading_hours_timezone or "America/New_York"
        now = datetime.now(tz=ZoneInfo(tz_name)).time()

        if not _is_within_hours(now, rule.trading_hours_start, rule.trading_hours_end):
            return RiskViolation(
                breach_type=RiskBreachType.TRADING_HOURS,
                message=(
                    f"Outside trading hours "
                    f"({rule.trading_hours_start}-{rule.trading_hours_end} {tz_name})"
                ),
                action=RiskAction.BLOCK,
            )
        return None


class AllowedSymbolsRule(RiskRuleEvaluator):
    def evaluate(
        self,
        rule: RiskRule,
        state: AccountRiskState,
        order: ProposedOrder | None,
    ) -> RiskViolation | None:
        if not rule.allowed_symbols or order is None:
            return None
        allowed = {s.upper() for s in rule.allowed_symbols}
        if order.symbol.upper() not in allowed:
            return RiskViolation(
                breach_type=RiskBreachType.ALLOWED_SYMBOLS,
                message=f"Symbol {order.symbol} not in allowed list",
                symbol=order.symbol,
                action=RiskAction.BLOCK,
            )
        return None


class BlockedSymbolsRule(RiskRuleEvaluator):
    def evaluate(
        self,
        rule: RiskRule,
        state: AccountRiskState,
        order: ProposedOrder | None,
    ) -> RiskViolation | None:
        if not rule.blocked_symbols or order is None:
            return None
        blocked = {s.upper() for s in rule.blocked_symbols}
        if order.symbol.upper() in blocked:
            return RiskViolation(
                breach_type=RiskBreachType.BLOCKED_SYMBOLS,
                message=f"Symbol {order.symbol} is blocked",
                symbol=order.symbol,
                action=RiskAction.BLOCK,
            )
        return None


class LeverageLimitRule(RiskRuleEvaluator):
    def evaluate(
        self,
        rule: RiskRule,
        state: AccountRiskState,
        order: ProposedOrder | None,
    ) -> RiskViolation | None:
        if rule.max_leverage is None:
            return None
        if state.current_leverage > rule.max_leverage:
            return RiskViolation(
                breach_type=RiskBreachType.LEVERAGE_LIMIT,
                message=f"Leverage {state.current_leverage}x exceeds limit {rule.max_leverage}x",
                current_value=state.current_leverage,
                limit_value=rule.max_leverage,
                action=RiskAction.BLOCK,
            )
        return None


def _is_within_hours(now: time, start: time, end: time) -> bool:
    if start <= end:
        return start <= now <= end
    return now >= start or now <= end


DEFAULT_EVALUATORS: list[RiskRuleEvaluator] = [
    KillSwitchRule(),
    DailyLossRule(),
    MaxDrawdownRule(),
    MaxPositionSizeRule(),
    MaxContractsRule(),
    TradingHoursRule(),
    AllowedSymbolsRule(),
    BlockedSymbolsRule(),
    LeverageLimitRule(),
]
