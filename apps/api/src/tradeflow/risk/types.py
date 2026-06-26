"""Risk engine domain types."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from uuid import UUID

from tradeflow.db.enums import OrderSide, RiskAction, RiskBreachType, RiskMonitorStatus


@dataclass(frozen=True)
class ProposedOrder:
    """Order about to be placed — input to pre-trade risk checks."""

    symbol: str
    side: OrderSide
    quantity: int
    price: Decimal | None = None
    notional_usd: Decimal | None = None


@dataclass
class AccountRiskState:
    """Real-time account risk state (Redis + in-memory)."""

    trading_account_id: UUID
    daily_pnl: Decimal = Decimal("0")
    peak_equity: Decimal = Decimal("0")
    current_equity: Decimal = Decimal("0")
    drawdown_usd: Decimal = Decimal("0")
    total_open_contracts: int = 0
    contracts_by_symbol: dict[str, int] = field(default_factory=dict)
    current_leverage: Decimal = Decimal("0")
    kill_switch_active: bool = False
    last_reset_at: datetime | None = None
    status: RiskMonitorStatus = RiskMonitorStatus.HEALTHY


@dataclass(frozen=True)
class RiskViolation:
    breach_type: RiskBreachType
    message: str
    current_value: Decimal | None = None
    limit_value: Decimal | None = None
    symbol: str | None = None
    action: RiskAction = RiskAction.BLOCK


@dataclass
class RiskCheckResult:
    allowed: bool
    violations: list[RiskViolation] = field(default_factory=list)
    status: RiskMonitorStatus = RiskMonitorStatus.HEALTHY

    @property
    def primary_violation(self) -> RiskViolation | None:
        return self.violations[0] if self.violations else None
