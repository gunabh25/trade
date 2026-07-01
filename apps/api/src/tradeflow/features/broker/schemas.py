"""Broker API schemas."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field

from tradeflow.db.enums import (
    BrokerType,
    ConnectionStatus,
    TradingAccountRole,
    TradingAccountStatus,
    TradingAccountType,
)


class CreateBrokerConnectionRequest(BaseModel):
    broker: BrokerType
    name: str = Field(min_length=1, max_length=100)
    credentials: dict[str, Any]


class BrokerConnectionResponse(BaseModel):
    id: UUID
    broker: BrokerType
    name: str
    status: ConnectionStatus
    last_connected_at: datetime | None
    last_error: str | None
    created_at: datetime


class BrokerHealthResponse(BaseModel):
    connection_id: UUID
    status: str
    connected: bool
    websocket_connected: bool
    latency_ms: float | None
    reconnect_attempts: int
    last_error: str | None


class BrokerAccountResponse(BaseModel):
    id: str
    name: str
    currency: str
    balance: Decimal
    equity: Decimal
    is_live: bool


class BrokerOrderResponse(BaseModel):
    id: str
    account_id: str
    symbol: str
    side: str
    order_type: str
    quantity: Decimal
    price: Decimal | None
    status: str
    filled_quantity: Decimal


class BrokerPositionResponse(BaseModel):
    id: str
    account_id: str
    symbol: str
    side: str
    quantity: Decimal
    entry_price: Decimal
    mark_price: Decimal
    unrealized_pnl: Decimal


class PlaceOrderRequest(BaseModel):
    account_id: str
    symbol: str
    side: str
    order_type: str
    quantity: Decimal = Field(gt=0)
    price: Decimal | None = None


class ModifyOrderRequest(BaseModel):
    quantity: Decimal | None = Field(default=None, gt=0)
    price: Decimal | None = None


class FlattenPositionRequest(BaseModel):
    account_id: str
    symbol: str


class BrokerCapabilitiesResponse(BaseModel):
    broker: str
    supports_rest: bool
    supports_websocket: bool
    supports_stream_market_data: bool
    supports_stream_orders: bool
    supports_stream_positions: bool
    supports_token_refresh: bool
    supports_webhook_inbound: bool
    max_orders_per_second: float
    supported_asset_classes: list[str]
    notes: str | None = None


class SupportedBrokersResponse(BaseModel):
    brokers: list[str]
    capabilities: list[BrokerCapabilitiesResponse] = Field(default_factory=list)


class TradingAccountResponse(BaseModel):
    id: UUID
    broker_connection_id: UUID
    external_account_id: str
    name: str
    broker: BrokerType
    account_type: TradingAccountType
    account_role: TradingAccountRole
    status: TradingAccountStatus
    currency: str
    balance: Decimal | None
    created_at: datetime
