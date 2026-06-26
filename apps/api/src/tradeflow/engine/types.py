"""Copy engine domain types — normalized leader events and copy decisions."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from enum import StrEnum
from typing import Any
from uuid import UUID

from tradeflow.db.enums import CopyEventAction, CopyMode, OrderLegType, OrderSide, OrderType


class LeaderEventType(StrEnum):
    ORDER_SUBMITTED = "order_submitted"
    ORDER_MODIFIED = "order_modified"
    ORDER_CANCELLED = "order_cancelled"
    FILL = "fill"
    PARTIAL_FILL = "partial_fill"


@dataclass(frozen=True)
class LeaderEvent:
    """Normalized leader order event — dedupe key is `id`."""

    id: str
    copy_group_id: UUID
    leader_account_id: UUID
    user_id: UUID
    event_type: LeaderEventType
    leader_order_id: str
    symbol: str
    side: OrderSide
    order_type: OrderType
    quantity: int
    price: Decimal | None = None
    stop_price: Decimal | None = None
    filled_quantity: int = 0
    avg_fill_price: Decimal | None = None
    parent_order_id: str | None = None
    leg_type: OrderLegType = OrderLegType.ENTRY
    timestamp: datetime | None = None
    raw: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class CopyDecision:
    """Planned action for a single follower."""

    follower_account_id: UUID
    follower_config_id: UUID
    action: CopyEventAction
    quantity: int
    side: OrderSide
    order_type: OrderType
    price: Decimal | None = None
    stop_price: Decimal | None = None
    leg_type: OrderLegType = OrderLegType.ENTRY
    skip: bool = False
    skip_reason: str | None = None
    parent_mapping_id: UUID | None = None


@dataclass
class CopyExecutionResult:
    """Outcome of executing a copy decision on one follower."""

    decision: CopyDecision
    success: bool
    follower_order_id: str | None = None
    follower_order_db_id: UUID | None = None
    follower_price: Decimal | None = None
    slippage: Decimal | None = None
    latency_ms: int = 0
    error: str | None = None
    partial_fill: bool = False
    filled_quantity: int = 0


@dataclass(frozen=True)
class FollowerContext:
    """Runtime context loaded for follower execution."""

    follower_account_id: UUID
    broker_connection_id: UUID
    external_account_id: str
    copy_mode: CopyMode
    sizing_value: Decimal
    enabled: bool
    status: str
    leader_balance: Decimal | None = None
    follower_balance: Decimal | None = None
