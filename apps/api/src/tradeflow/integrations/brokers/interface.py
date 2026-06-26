"""Abstract broker adapter interface (Interface Segregation / Dependency Inversion)."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from tradeflow.integrations.brokers.types import (
    BrokerAccount,
    BrokerCredentials,
    BrokerOrder,
    BrokerPosition,
    ConnectionHealth,
    ModifyOrderRequest,
    PlaceOrderRequest,
)


class BrokerAdapter(ABC):
    """Contract every broker integration must fulfill."""

    @property
    @abstractmethod
    def broker_name(self) -> str:
        """Human-readable broker identifier."""

    @abstractmethod
    async def connect(self, credentials: BrokerCredentials) -> None:
        """Establish connection to the broker."""

    @abstractmethod
    async def disconnect(self) -> None:
        """Gracefully tear down connection and WebSocket streams."""

    @abstractmethod
    async def fetch_accounts(self) -> list[BrokerAccount]:
        """Return trading accounts available under this connection."""

    @abstractmethod
    async def fetch_orders(self, account_id: str) -> list[BrokerOrder]:
        """Return open and recent orders for an account."""

    @abstractmethod
    async def fetch_positions(self, account_id: str) -> list[BrokerPosition]:
        """Return open positions for an account."""

    @abstractmethod
    async def place_order(self, request: PlaceOrderRequest) -> BrokerOrder:
        """Submit a new order."""

    @abstractmethod
    async def modify_order(self, order_id: str, request: ModifyOrderRequest) -> BrokerOrder:
        """Modify an existing order."""

    @abstractmethod
    async def cancel_order(self, order_id: str) -> BrokerOrder:
        """Cancel an open order."""

    @abstractmethod
    def get_health(self) -> ConnectionHealth:
        """Return current connection health snapshot."""

    async def subscribe_market_data(
        self,
        symbols: list[str],
        handler: Any,
    ) -> None:
        """Optional: subscribe to real-time quotes via WebSocket."""
        _ = (symbols, handler)
