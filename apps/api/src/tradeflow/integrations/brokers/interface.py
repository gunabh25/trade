"""Abstract broker adapter interface (Interface Segregation / Dependency Inversion)."""

from __future__ import annotations

from abc import ABC, abstractmethod

from tradeflow.integrations.brokers.capabilities import BrokerCapabilities
from tradeflow.integrations.brokers.types import (
    BrokerAccount,
    BrokerCredentials,
    BrokerOrder,
    BrokerPosition,
    ConnectionHealth,
    ModifyOrderRequest,
    PlaceOrderRequest,
    StreamHandler,
    StreamSubscription,
)


class BrokerAdapter(ABC):
    """Contract every broker integration must fulfill."""

    @property
    @abstractmethod
    def broker_name(self) -> str:
        """Human-readable broker identifier."""

    @property
    @abstractmethod
    def capabilities(self) -> BrokerCapabilities:
        """Feature detection for this broker."""

    @abstractmethod
    async def connect(self, credentials: BrokerCredentials) -> None:
        """Establish connection to the broker."""

    @abstractmethod
    async def disconnect(self) -> None:
        """Gracefully tear down connection and WebSocket streams."""

    async def refresh_token(self) -> None:
        """Refresh OAuth/API token if supported."""
        return None

    @abstractmethod
    async def validate_connection(self) -> bool:
        """Lightweight health ping — returns True if credentials and API are valid."""

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
    async def flatten_position(self, account_id: str, symbol: str) -> BrokerOrder:
        """Close an entire position via market order."""

    @abstractmethod
    async def stream_market_data(
        self,
        symbols: list[str],
        handler: StreamHandler,
    ) -> StreamSubscription:
        """Subscribe to real-time quotes."""

    @abstractmethod
    async def stream_orders(self, account_id: str, handler: StreamHandler) -> StreamSubscription:
        """Subscribe to order updates."""

    @abstractmethod
    async def stream_positions(self, account_id: str, handler: StreamHandler) -> StreamSubscription:
        """Subscribe to position updates."""

    @abstractmethod
    def get_health(self) -> ConnectionHealth:
        """Return current connection health snapshot."""
