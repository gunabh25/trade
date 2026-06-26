"""Base broker adapter with retry, reconnect, logging, metrics, and health monitoring."""

from __future__ import annotations

import time
from abc import abstractmethod
from collections.abc import Awaitable, Callable
from datetime import UTC, datetime
from typing import Any

from tradeflow.core.logging import get_logger
from tradeflow.integrations.brokers.exceptions import (
    BrokerConnectionError,
    BrokerNotConnectedError,
    BrokerNotSupportedError,
    BrokerTransientError,
)
from tradeflow.integrations.brokers.interface import BrokerAdapter
from tradeflow.integrations.brokers.metrics import get_broker_metrics
from tradeflow.integrations.brokers.retry import RetryPolicy, with_retry
from tradeflow.integrations.brokers.types import (
    BrokerCredentials,
    BrokerHealthStatus,
    ConnectionHealth,
    StreamHandler,
    StreamSubscription,
)
from tradeflow.integrations.brokers.websocket import BrokerWebSocketManager

logger = get_logger(__name__)


class BaseBrokerAdapter(BrokerAdapter):
    """Template method base class — DRY for connection lifecycle concerns."""

    def __init__(
        self,
        *,
        retry_policy: RetryPolicy | None = None,
        auto_reconnect: bool = True,
        max_reconnect_attempts: int = 5,
    ) -> None:
        self._retry_policy = retry_policy or RetryPolicy()
        self._auto_reconnect = auto_reconnect
        self._max_reconnect_attempts = max_reconnect_attempts
        self._credentials: BrokerCredentials | None = None
        self._health = ConnectionHealth()
        self._websocket = BrokerWebSocketManager(self.broker_name)
        self._stream_subscriptions: list[StreamSubscription] = []

    @property
    def websocket(self) -> BrokerWebSocketManager:
        return self._websocket

    async def connect(self, credentials: BrokerCredentials) -> None:
        self._credentials = credentials
        await with_retry(
            lambda: self._connect_impl(credentials),
            policy=self._retry_policy,
            operation_name=f"{self.broker_name}.connect",
        )
        self._health.connected = True
        self._health.status = BrokerHealthStatus.HEALTHY
        self._health.last_connected_at = datetime.now(tz=UTC)
        self._health.last_error = None
        self._health.reconnect_attempts = 0
        logger.info("broker_connected", broker=self.broker_name)

    async def disconnect(self) -> None:
        for sub in self._stream_subscriptions:
            await sub.unsubscribe()
        self._stream_subscriptions.clear()
        await self._websocket.disconnect()
        await self._disconnect_impl()
        self._health.connected = False
        self._health.status = BrokerHealthStatus.DISCONNECTED
        self._health.websocket_connected = False
        logger.info("broker_disconnected", broker=self.broker_name)

    async def refresh_token(self) -> None:
        if not self.capabilities.supports_token_refresh:
            raise BrokerNotSupportedError(f"{self.broker_name} does not support token refresh")
        await self._execute("refresh_token", self._refresh_token_impl)

    async def validate_connection(self) -> bool:
        try:
            await self._execute("validate_connection", self._validate_connection_impl)
            return True
        except Exception:
            return False

    def get_health(self) -> ConnectionHealth:
        self._health.websocket_connected = self._websocket.is_connected
        return self._health

    async def stream_market_data(
        self,
        symbols: list[str],
        handler: StreamHandler,
    ) -> StreamSubscription:
        if not self.capabilities.supports_stream_market_data:
            raise BrokerNotSupportedError(
                f"{self.broker_name} does not support market data streams",
            )
        sub = await self._stream_market_data_impl(symbols, handler)
        self._stream_subscriptions.append(sub)
        return sub

    async def stream_orders(self, account_id: str, handler: StreamHandler) -> StreamSubscription:
        if not self.capabilities.supports_stream_orders:
            raise BrokerNotSupportedError(f"{self.broker_name} does not support order streams")
        sub = await self._stream_orders_impl(account_id, handler)
        self._stream_subscriptions.append(sub)
        return sub

    async def stream_positions(self, account_id: str, handler: StreamHandler) -> StreamSubscription:
        if not self.capabilities.supports_stream_positions:
            raise BrokerNotSupportedError(f"{self.broker_name} does not support position streams")
        sub = await self._stream_positions_impl(account_id, handler)
        self._stream_subscriptions.append(sub)
        return sub

    async def flatten_position(self, account_id: str, symbol: str) -> Any:
        if not self.capabilities.supports_flatten_position:
            raise BrokerNotSupportedError(f"{self.broker_name} does not support flatten_position")
        return await self._execute(
            "flatten_position",
            lambda: self._flatten_position_impl(account_id, symbol),
        )

    async def _ensure_connected(self) -> None:
        if self._health.connected:
            return
        if not self._auto_reconnect or self._credentials is None:
            raise BrokerNotConnectedError(f"{self.broker_name} is not connected")
        if self._health.reconnect_attempts >= self._max_reconnect_attempts:
            raise BrokerConnectionError(
                f"{self.broker_name} reconnect limit exceeded ({self._max_reconnect_attempts})",
            )
        self._health.reconnect_attempts += 1
        logger.warning(
            "broker_auto_reconnect",
            broker=self.broker_name,
            attempt=self._health.reconnect_attempts,
        )
        try:
            await self.connect(self._credentials)
        except BrokerTransientError as exc:
            self._health.status = BrokerHealthStatus.ERROR
            self._health.last_error = str(exc)
            raise

    async def _execute(
        self,
        operation_name: str,
        operation: Callable[[], Awaitable[Any]],
    ) -> Any:
        await self._ensure_connected()
        start = time.perf_counter()
        try:
            result = await with_retry(
                operation,
                policy=self._retry_policy,
                operation_name=f"{self.broker_name}.{operation_name}",
            )
            latency = (time.perf_counter() - start) * 1000
            self._health.latency_ms = latency
            self._health.status = BrokerHealthStatus.HEALTHY
            get_broker_metrics().record(
                f"{self.broker_name}.{operation_name}",
                latency_ms=latency,
            )
            return result
        except Exception as exc:
            latency = (time.perf_counter() - start) * 1000
            self._health.status = BrokerHealthStatus.ERROR
            self._health.last_error = str(exc)
            get_broker_metrics().record(
                f"{self.broker_name}.{operation_name}",
                latency_ms=latency,
                error=True,
            )
            logger.error(
                "broker_operation_failed",
                broker=self.broker_name,
                operation=operation_name,
                error=str(exc),
            )
            raise

    @abstractmethod
    async def _connect_impl(self, credentials: BrokerCredentials) -> None:
        """Broker-specific connection logic."""

    async def _disconnect_impl(self) -> None:
        """Optional broker-specific teardown."""

    async def _refresh_token_impl(self) -> None:
        raise BrokerNotSupportedError(f"{self.broker_name} token refresh not implemented")

    async def _validate_connection_impl(self) -> None:
        await self._fetch_accounts_impl()

    async def _flatten_position_impl(self, account_id: str, symbol: str) -> Any:
        raise BrokerNotSupportedError(f"{self.broker_name} flatten_position not implemented")

    async def _stream_market_data_impl(
        self,
        symbols: list[str],
        handler: StreamHandler,
    ) -> StreamSubscription:
        raise BrokerNotSupportedError(f"{self.broker_name} stream_market_data not implemented")

    async def _stream_orders_impl(
        self,
        account_id: str,
        handler: StreamHandler,
    ) -> StreamSubscription:
        raise BrokerNotSupportedError(f"{self.broker_name} stream_orders not implemented")

    async def _stream_positions_impl(
        self,
        account_id: str,
        handler: StreamHandler,
    ) -> StreamSubscription:
        raise BrokerNotSupportedError(f"{self.broker_name} stream_positions not implemented")

    async def _fetch_accounts_impl(self) -> Any:
        raise BrokerNotSupportedError(f"{self.broker_name} fetch_accounts not implemented")

    async def _connect_websocket(self, url: str, *, headers: dict[str, str] | None = None) -> None:
        await self._websocket.connect(url, headers=headers)
        self._health.websocket_connected = True
