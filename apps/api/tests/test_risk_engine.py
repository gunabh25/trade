"""Risk engine unit tests."""

from __future__ import annotations

from datetime import time
from decimal import Decimal
from uuid import uuid4

import pytest

from tradeflow.db.enums import OrderSide, RiskAction, RiskBreachType
from tradeflow.db.models.risk import RiskRule
from tradeflow.risk.rules import (
    BlockedSymbolsRule,
    DailyLossRule,
    KillSwitchRule,
    MaxContractsRule,
    MaxDrawdownRule,
    TradingHoursRule,
)
from tradeflow.risk.types import AccountRiskState, ProposedOrder


def _rule(**kwargs: object) -> RiskRule:
    rule = RiskRule(
        id=uuid4(),
        user_id=uuid4(),
        trading_account_id=uuid4(),
    )
    for key, value in kwargs.items():
        setattr(rule, key, value)
    return rule


def _state(**kwargs: object) -> AccountRiskState:
    state = AccountRiskState(trading_account_id=uuid4())
    for key, value in kwargs.items():
        setattr(state, key, value)
    return state


def test_kill_switch_blocks_all() -> None:
    rule = _rule(kill_switch_active=True)
    state = _state()
    violation = KillSwitchRule().evaluate(rule, state, None)
    assert violation is not None
    assert violation.breach_type == RiskBreachType.KILL_SWITCH


def test_daily_loss_breach() -> None:
    rule = _rule(daily_loss_limit_usd=Decimal("500"))
    state = _state(daily_pnl=Decimal("-600"))
    violation = DailyLossRule().evaluate(rule, state, None)
    assert violation is not None
    assert violation.breach_type == RiskBreachType.DAILY_LOSS
    assert violation.action == RiskAction.STOP_COPYING


def test_max_drawdown_breach() -> None:
    rule = _rule(trailing_drawdown_limit_usd=Decimal("1000"))
    state = _state(drawdown_usd=Decimal("1500"))
    violation = MaxDrawdownRule().evaluate(rule, state, None)
    assert violation is not None
    assert violation.breach_type == RiskBreachType.MAX_DRAWDOWN
    assert violation.action == RiskAction.FLATTEN


def test_max_contracts_per_symbol() -> None:
    rule = _rule(max_contracts_per_symbol=5)
    state = _state(contracts_by_symbol={"ES": 3}, total_open_contracts=3)
    order = ProposedOrder(symbol="ES", side=OrderSide.BUY, quantity=3)
    violation = MaxContractsRule().evaluate(rule, state, order)
    assert violation is not None
    assert violation.breach_type == RiskBreachType.MAX_CONTRACTS_PER_SYMBOL


def test_blocked_symbols() -> None:
    rule = _rule(blocked_symbols=["DOGE", "SHIB"])
    state = _state()
    order = ProposedOrder(symbol="DOGE", side=OrderSide.BUY, quantity=1)
    violation = BlockedSymbolsRule().evaluate(rule, state, order)
    assert violation is not None
    assert violation.breach_type == RiskBreachType.BLOCKED_SYMBOLS


def test_trading_hours_outside_window() -> None:
    rule = _rule(
        trading_hours_start=time(3, 0),
        trading_hours_end=time(4, 0),
        trading_hours_timezone="UTC",
    )
    state = _state()
    order = ProposedOrder(symbol="ES", side=OrderSide.BUY, quantity=1)
    violation = TradingHoursRule().evaluate(rule, state, order)
    assert violation is not None
    assert violation.breach_type == RiskBreachType.TRADING_HOURS


@pytest.mark.asyncio
async def test_risk_state_store_roundtrip(redis_client) -> None:
    from tradeflow.risk.state import RiskStateStore

    store = RiskStateStore(redis_client)
    account_id = uuid4()
    state = await store.update_pnl(
        account_id,
        daily_pnl=Decimal("-100"),
        current_equity=Decimal("9900"),
    )
    loaded = await store.get_state(account_id)
    assert loaded.daily_pnl == state.daily_pnl
    assert loaded.current_equity == Decimal("9900")


def test_risk_evaluator_allows_when_no_violations() -> None:
    from tradeflow.risk.evaluator import RiskEvaluator

    evaluator = RiskEvaluator(state_store=_FakeStateStore())
    rule = _rule(enabled=True, daily_loss_limit_usd=Decimal("1000"))
    state = _state(daily_pnl=Decimal("-100"))
    result = evaluator._evaluate(rule, state, None)
    assert result.allowed is True


class _FakeStateStore:
    async def get_state(self, account_id: object) -> AccountRiskState:
        return AccountRiskState(trading_account_id=uuid4())
