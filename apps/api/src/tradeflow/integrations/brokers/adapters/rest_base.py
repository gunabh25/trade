"""Shared helpers for REST-based broker adapters."""

from __future__ import annotations

from tradeflow.integrations.brokers.base import BaseBrokerAdapter
from tradeflow.integrations.brokers.exceptions import BrokerConnectionError, BrokerNotSupportedError
from tradeflow.integrations.brokers.types import (
    BrokerAccount,
    BrokerCredentials,
    BrokerOrder,
    BrokerPosition,
    ModifyOrderRequest,
    PlaceOrderRequest,
)


class RestBrokerAdapter(BaseBrokerAdapter):
    """Base for HTTP REST brokers — validates credentials, stubs unimplemented trading ops."""

    required_credential_keys: tuple[str, ...] = ("api_key",)

    async def _connect_impl(self, credentials: BrokerCredentials) -> None:
        missing = [k for k in self.required_credential_keys if not credentials.data.get(k)]
        if missing:
            msg = f"Missing credentials for {self.broker_name}: {', '.join(missing)}"
            raise BrokerConnectionError(msg)
        await self._connect_websocket(f"wss://{self.broker_name}.example/stream")

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

    async def _fetch_accounts_impl(self) -> list[BrokerAccount]:
        raise BrokerNotSupportedError(f"{self.broker_name} fetch_accounts not yet implemented")

    async def _fetch_orders_impl(self, account_id: str) -> list[BrokerOrder]:
        raise BrokerNotSupportedError(f"{self.broker_name} fetch_orders not yet implemented")

    async def _fetch_positions_impl(self, account_id: str) -> list[BrokerPosition]:
        raise BrokerNotSupportedError(f"{self.broker_name} fetch_positions not yet implemented")

    async def _place_order_impl(self, request: PlaceOrderRequest) -> BrokerOrder:
        raise BrokerNotSupportedError(f"{self.broker_name} place_order not yet implemented")

    async def _modify_order_impl(self, order_id: str, request: ModifyOrderRequest) -> BrokerOrder:
        raise BrokerNotSupportedError(f"{self.broker_name} modify_order not yet implemented")

    async def _cancel_order_impl(self, order_id: str) -> BrokerOrder:
        raise BrokerNotSupportedError(f"{self.broker_name} cancel_order not yet implemented")
