"""Risk management API schemas."""

from __future__ import annotations

from datetime import datetime, time
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, Field

from tradeflow.db.enums import RiskAction, RiskBreachType, RiskMonitorStatus


class RiskRuleConfig(BaseModel):
    """User-configurable risk rule settings."""

    name: str = Field(default="Default", max_length=100)
    enabled: bool = True

    daily_loss_limit_usd: Decimal | None = Field(default=None, ge=0)
    trailing_drawdown_limit_usd: Decimal | None = Field(default=None, ge=0)
    max_position_size_usd: Decimal | None = Field(default=None, ge=0)
    max_contracts_per_symbol: int | None = Field(default=None, ge=1)
    max_total_contracts: int | None = Field(default=None, ge=1)
    max_leverage: Decimal | None = Field(default=None, ge=0)

    allowed_symbols: list[str] | None = None
    blocked_symbols: list[str] | None = None

    trading_hours_start: time | None = None
    trading_hours_end: time | None = None
    trading_hours_timezone: str = "America/New_York"
    session_reset_time: time | None = None

    auto_flatten_on_breach: bool = True
    auto_stop_copying_on_breach: bool = True


class CreateRiskRuleRequest(RiskRuleConfig):
    trading_account_id: UUID


class UpdateRiskRuleRequest(RiskRuleConfig):
    pass


class RiskRuleResponse(BaseModel):
    id: UUID
    trading_account_id: UUID
    name: str
    enabled: bool
    kill_switch_active: bool

    daily_loss_limit_usd: Decimal | None
    trailing_drawdown_limit_usd: Decimal | None
    max_position_size_usd: Decimal | None
    max_contracts_per_symbol: int | None
    max_total_contracts: int | None
    max_leverage: Decimal | None

    allowed_symbols: list[str] | None
    blocked_symbols: list[str] | None

    trading_hours_start: time | None
    trading_hours_end: time | None
    trading_hours_timezone: str | None
    session_reset_time: time | None

    auto_flatten_on_breach: bool
    auto_stop_copying_on_breach: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class RiskBreachResponse(BaseModel):
    id: UUID
    trading_account_id: UUID
    breach_type: RiskBreachType
    action_taken: RiskAction
    message: str
    current_value: Decimal | None
    limit_value: Decimal | None
    symbol: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


class RiskMonitorStatusResponse(BaseModel):
    trading_account_id: UUID
    status: RiskMonitorStatus
    daily_pnl: Decimal | None
    drawdown_usd: Decimal | None
    peak_equity: Decimal | None
    current_equity: Decimal | None
    total_open_contracts: int | None
    current_leverage: Decimal | None
    kill_switch_active: bool
    checked_at: datetime


class KillSwitchRequest(BaseModel):
    active: bool
