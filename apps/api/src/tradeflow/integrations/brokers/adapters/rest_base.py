"""Shared production REST broker adapter base."""

from __future__ import annotations

from abc import abstractmethod
from decimal import Decimal

from tradeflow.integrations.brokers.base import BaseBrokerAdapter
from tradeflow.integrations.brokers.exceptions import BrokerConnectionError, BrokerNotSupportedError
from tradeflow.integrations.brokers.http_client import BrokerHttpClient
from tradeflow.integrations.brokers.pool import BrokerHttpPool
from tradeflow.integrations.brokers.types import (
    BrokerAccount,
    BrokerCredentials,
    BrokerOrder,
    BrokerOrderSide,
    BrokerOrderType,
    BrokerPosition,
    ModifyOrderRequest,
    PlaceOrderRequest,
    StreamHandler,
    StreamSubscription,
)


class RestBrokerAdapter(BaseBrokerAdapter):
    """Production REST adapter — HTTP pooling, rate limits, normalized errors."""

    required_credential_keys: tuple[str, ...] = ("api_key",)
    default_base_url: str = ""
    websocket_url: str | None = None

    def __init__(self, **kwargs: object) -> None:
        super().__init__(**kwargs)  # type: ignore[arg-type]
        self._http: BrokerHttpClient | None = None
        self._pool: BrokerHttpPool | None = None
        self._account_id: str | None = None

    async def _connect_impl(self, credentials: BrokerCredentials) -> None:
        missing = [k for k in self.required_credential_keys if not credentials.data.get(k)]
        if missing:
            msg = f"Missing credentials for {self.broker_name}: {', '.join(missing)}"
            raise BrokerConnectionError(msg)
        base_url = str(credentials.data.get("base_url") or self.default_base_url)
        if not base_url:
            msg = f"No base_url configured for {self.broker_name}"
            raise BrokerConnectionError(msg)
        self._pool = BrokerHttpPool(base_url=base_url)
        self._http = self._build_http_client(credentials, base_url)
        self._account_id = credentials.data.get("account_id")
        if self.websocket_url:
            await self._connect_websocket(self.websocket_url)

    async def _disconnect_impl(self) -> None:
        if self._http is not None:
            await self._http.close()
            self._http = None
        self._pool = None

    @abstractmethod
    def _build_http_client(self, credentials: BrokerCredentials, base_url: str) -> BrokerHttpClient:
        """Construct signed HTTP client for the broker."""

    def _http_client(self) -> BrokerHttpClient:
        if self._http is None:
            raise BrokerConnectionError(f"{self.broker_name} HTTP client not initialized")
        return self._http

    async def fetch_accounts(self) -> list[BrokerAccount]:
        return await self._execute("fetch_accounts", self._fetch_accounts_impl)

    async def fetch_orders(self, account_id: str) -> list[BrokerOrder]:
        return await self._execute(
            "fetch_orders",
            lambda: self._fetch_orders_impl(account_id),
        )

    async def fetch_positions(self, account_id: str) -> list[BrokerPosition]:
        return await self._execute(
            "fetch_positions",
            lambda: self._fetch_positions_impl(account_id),
        )

    async def place_order(self, request: PlaceOrderRequest) -> BrokerOrder:
        return await self._execute("place_order", lambda: self._place_order_impl(request))

    async def modify_order(self, order_id: str, request: ModifyOrderRequest) -> BrokerOrder:
        return await self._execute(
            "modify_order",
            lambda: self._modify_order_impl(order_id, request),
        )

    async def cancel_order(self, order_id: str) -> BrokerOrder:
        return await self._execute("cancel_order", lambda: self._cancel_order_impl(order_id))

    async def _flatten_position_impl(self, account_id: str, symbol: str) -> BrokerOrder:
        positions = await self._fetch_positions_impl(account_id)
        position = next((p for p in positions if p.symbol == symbol), None)
        if position is None:
            msg = f"No open position for {symbol}"
            raise BrokerNotSupportedError(msg)
        close_side = BrokerOrderSide.SELL if position.side.value == "long" else BrokerOrderSide.BUY
        return await self._place_order_impl(
            PlaceOrderRequest(
                account_id=account_id,
                symbol=symbol,
                side=close_side,
                order_type=BrokerOrderType.MARKET,
                quantity=position.quantity,
                metadata={"reduce_only": True},
            ),
        )

    async def _stream_orders_impl(
        self,
        account_id: str,
        handler: StreamHandler,
    ) -> StreamSubscription:
        if not self.websocket_url:
            raise BrokerNotSupportedError(f"{self.broker_name} has no websocket URL configured")
        return await self.websocket.subscribe(f"orders:{account_id}", handler)

    async def _stream_positions_impl(
        self,
        account_id: str,
        handler: StreamHandler,
    ) -> StreamSubscription:
        if not self.websocket_url:
            raise BrokerNotSupportedError(f"{self.broker_name} has no websocket URL configured")
        return await self.websocket.subscribe(f"positions:{account_id}", handler)

    async def _stream_market_data_impl(
        self,
        symbols: list[str],
        handler: StreamHandler,
    ) -> StreamSubscription:
        if not self.websocket_url:
            raise BrokerNotSupportedError(f"{self.broker_name} has no websocket URL configured")
        channel = f"market:{','.join(symbols)}"
        return await self.websocket.subscribe(channel, handler)

    @staticmethod
    def _decimal(value: object, default: str = "0") -> Decimal:
        if value is None:
            return Decimal(default)
        return Decimal(str(value))
