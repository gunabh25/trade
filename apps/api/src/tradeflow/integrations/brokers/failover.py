"""Failover wrapper — route to secondary broker when primary fails."""

from __future__ import annotations

from tradeflow.core.logging import get_logger
from tradeflow.integrations.brokers.capabilities import BrokerCapabilities
from tradeflow.integrations.brokers.exceptions import BrokerConnectionError, BrokerError
from tradeflow.integrations.brokers.interface import BrokerAdapter
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

logger = get_logger(__name__)


class FailoverBrokerAdapter(BrokerAdapter):
    """Primary/secondary failover — attempts secondary on connection/ transient errors."""

    def __init__(
        self,
        primary: BrokerAdapter,
        secondary: BrokerAdapter,
        *,
        broker_name: str | None = None,
    ) -> None:
        self._primary = primary
        self._secondary = secondary
        self._active: BrokerAdapter = primary
        self._broker_name = broker_name or f"{primary.broker_name}_failover"

    @property
    def broker_name(self) -> str:
        return self._broker_name

    @property
    def capabilities(self) -> BrokerCapabilities:
        primary_caps = self._primary.capabilities
        secondary_caps = self._secondary.capabilities
        return BrokerCapabilities(
            supports_rest=primary_caps.supports_rest or secondary_caps.supports_rest,
            supports_websocket=primary_caps.supports_websocket or secondary_caps.supports_websocket,
            supports_market_orders=primary_caps.supports_market_orders,
            supports_limit_orders=primary_caps.supports_limit_orders,
            supports_stop_orders=primary_caps.supports_stop_orders,
            supports_modify_order=primary_caps.supports_modify_order,
            supports_cancel_order=primary_caps.supports_cancel_order,
            supports_flatten_position=primary_caps.supports_flatten_position,
            supports_token_refresh=primary_caps.supports_token_refresh,
            supports_stream_market_data=primary_caps.supports_stream_market_data,
            supports_stream_orders=primary_caps.supports_stream_orders,
            supports_stream_positions=primary_caps.supports_stream_positions,
            supports_failover=True,
            notes="Failover wrapper",
        )

    async def connect(self, credentials: BrokerCredentials) -> None:
        try:
            await self._primary.connect(credentials)
            self._active = self._primary
        except BrokerError as exc:
            logger.warning("failover_primary_connect_failed", error=str(exc))
            await self._secondary.connect(credentials)
            self._active = self._secondary

    async def disconnect(self) -> None:
        await self._primary.disconnect()
        await self._secondary.disconnect()
        self._active = self._primary

    async def refresh_token(self) -> None:
        await self._active.refresh_token()

    async def validate_connection(self) -> bool:
        return await self._active.validate_connection()

    async def fetch_accounts(self) -> list[BrokerAccount]:
        return await self._with_failover(lambda a: a.fetch_accounts())

    async def fetch_orders(self, account_id: str) -> list[BrokerOrder]:
        return await self._with_failover(lambda a: a.fetch_orders(account_id))

    async def fetch_positions(self, account_id: str) -> list[BrokerPosition]:
        return await self._with_failover(lambda a: a.fetch_positions(account_id))

    async def place_order(self, request: PlaceOrderRequest) -> BrokerOrder:
        return await self._with_failover(lambda a: a.place_order(request))

    async def modify_order(self, order_id: str, request: ModifyOrderRequest) -> BrokerOrder:
        return await self._with_failover(lambda a: a.modify_order(order_id, request))

    async def cancel_order(self, order_id: str) -> BrokerOrder:
        return await self._with_failover(lambda a: a.cancel_order(order_id))

    async def flatten_position(self, account_id: str, symbol: str) -> BrokerOrder:
        return await self._with_failover(lambda a: a.flatten_position(account_id, symbol))

    async def stream_market_data(
        self,
        symbols: list[str],
        handler: StreamHandler,
    ) -> StreamSubscription:
        return await self._active.stream_market_data(symbols, handler)

    async def stream_orders(self, account_id: str, handler: StreamHandler) -> StreamSubscription:
        return await self._active.stream_orders(account_id, handler)

    async def stream_positions(self, account_id: str, handler: StreamHandler) -> StreamSubscription:
        return await self._active.stream_positions(account_id, handler)

    def get_health(self) -> ConnectionHealth:
        health = self._active.get_health()
        health.metadata = {"active": self._active.broker_name}  # type: ignore[attr-defined]
        return health

    async def _with_failover(self, operation: object) -> object:
        if not callable(operation):
            msg = "operation must be callable"
            raise TypeError(msg)
        try:
            return await operation(self._active)  # type: ignore[misc,no-any-return]
        except BrokerConnectionError:
            if self._active is self._secondary:
                raise
            logger.warning("failover_switching_to_secondary", primary=self._primary.broker_name)
            self._active = self._secondary
            return await operation(self._active)  # type: ignore[misc,no-any-return]
