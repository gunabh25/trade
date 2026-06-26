"""Broker integration domain types."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from enum import StrEnum
from typing import Any
from uuid import UUID


class BrokerHealthStatus(StrEnum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    DISCONNECTED = "disconnected"
    ERROR = "error"


class BrokerOrderSide(StrEnum):
    BUY = "buy"
    SELL = "sell"


class BrokerOrderType(StrEnum):
    MARKET = "market"
    LIMIT = "limit"
    STOP = "stop"
    STOP_LIMIT = "stop_limit"


class BrokerOrderStatus(StrEnum):
    PENDING = "pending"
    OPEN = "open"
    PARTIAL = "partial"
    FILLED = "filled"
    CANCELED = "canceled"
    REJECTED = "rejected"


class BrokerPositionSide(StrEnum):
    LONG = "long"
    SHORT = "short"


@dataclass(frozen=True)
class BrokerCredentials:
    """Decrypted credentials passed to adapters."""

    data: dict[str, Any]


@dataclass(frozen=True)
class BrokerAccount:
    id: str
    name: str
    currency: str = "USD"
    balance: Decimal = Decimal("0")
    equity: Decimal = Decimal("0")
    is_live: bool = False
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class BrokerOrder:
    id: str
    account_id: str
    symbol: str
    side: BrokerOrderSide
    order_type: BrokerOrderType
    quantity: Decimal
    price: Decimal | None
    status: BrokerOrderStatus
    filled_quantity: Decimal = Decimal("0")
    created_at: datetime | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class BrokerPosition:
    id: str
    account_id: str
    symbol: str
    side: BrokerPositionSide
    quantity: Decimal
    entry_price: Decimal
    mark_price: Decimal
    unrealized_pnl: Decimal = Decimal("0")
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class PlaceOrderRequest:
    account_id: str
    symbol: str
    side: BrokerOrderSide
    order_type: BrokerOrderType
    quantity: Decimal
    price: Decimal | None = None
    stop_price: Decimal | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ModifyOrderRequest:
    quantity: Decimal | None = None
    price: Decimal | None = None
    stop_price: Decimal | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class ConnectionHealth:
    status: BrokerHealthStatus = BrokerHealthStatus.DISCONNECTED
    connected: bool = False
    last_connected_at: datetime | None = None
    last_error: str | None = None
    reconnect_attempts: int = 0
    websocket_connected: bool = False
    latency_ms: float | None = None


@dataclass(frozen=True)
class BrokerConnectionContext:
    """Runtime context for an active broker session."""

    connection_id: UUID
    broker_type: str
    user_id: UUID
