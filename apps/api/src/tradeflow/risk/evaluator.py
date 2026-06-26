"""Risk evaluator — orchestrates all rule checks."""

from __future__ import annotations

from uuid import UUID

from tradeflow.core.logging import get_logger
from tradeflow.db.enums import RiskMonitorStatus
from tradeflow.db.models.risk import RiskRule
from tradeflow.risk.rules import DEFAULT_EVALUATORS, RiskRuleEvaluator
from tradeflow.risk.state import RiskStateStore
from tradeflow.risk.types import AccountRiskState, ProposedOrder, RiskCheckResult, RiskViolation

logger = get_logger(__name__)


class RiskEvaluator:
    """Evaluates all configured risk rules against current account state."""

    def __init__(
        self,
        state_store: RiskStateStore,
        evaluators: list[RiskRuleEvaluator] | None = None,
    ) -> None:
        self._state = state_store
        self._evaluators = evaluators or DEFAULT_EVALUATORS

    async def check_pre_trade(
        self,
        rule: RiskRule,
        account_id: UUID,
        order: ProposedOrder,
    ) -> RiskCheckResult:
        """Pre-trade gate — called before every copy execution."""
        if not rule.enabled:
            return RiskCheckResult(allowed=True)

        state = await self._state.get_state(account_id)
        return self._evaluate(rule, state, order)

    async def check_account(
        self,
        rule: RiskRule,
        account_id: UUID,
    ) -> RiskCheckResult:
        """Continuous monitoring — no proposed order."""
        if not rule.enabled:
            return RiskCheckResult(allowed=True)

        state = await self._state.get_state(account_id)
        return self._evaluate(rule, state, order=None)

    def _evaluate(
        self,
        rule: RiskRule,
        state: AccountRiskState,
        order: ProposedOrder | None,
    ) -> RiskCheckResult:
        violations: list[RiskViolation] = []

        for evaluator in self._evaluators:
            violation = evaluator.evaluate(rule, state, order)
            if violation is not None:
                violations.append(violation)

        if not violations:
            return RiskCheckResult(allowed=True, status=RiskMonitorStatus.HEALTHY)

        status = RiskMonitorStatus.BREACHED
        if any(v.breach_type.value == "kill_switch" for v in violations):
            status = RiskMonitorStatus.KILL_SWITCH

        logger.warning(
            "risk_violation_detected",
            account_id=str(state.trading_account_id),
            violations=[v.breach_type.value for v in violations],
        )
        return RiskCheckResult(allowed=False, violations=violations, status=status)
