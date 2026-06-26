"""TradingView webhook adapter."""

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


class TradingViewWebhookAdapter(BaseBrokerAdapter):
    """Receives signals via webhook — outbound-only, no polling."""

    @property
    def broker_name(self) -> str:
        return "tradingview"

    async def _connect_impl(self, credentials: BrokerCredentials) -> None:
        if not credentials.data.get("webhook_secret"):
            raise BrokerConnectionError("TradingView adapter requires webhook_secret")

    async def fetch_accounts(self) -> list[BrokerAccount]:
        async def _fetch() -> list[BrokerAccount]:
            return []

        return await self._execute("fetch_accounts", _fetch)

    async def fetch_orders(self, account_id: str) -> list[BrokerOrder]:
        async def _fetch() -> list[BrokerOrder]:
            return []

        return await self._execute("fetch_orders", _fetch)

    async def fetch_positions(self, account_id: str) -> list[BrokerPosition]:
        async def _fetch() -> list[BrokerPosition]:
            return []

        return await self._execute("fetch_positions", _fetch)

    async def place_order(self, request: PlaceOrderRequest) -> BrokerOrder:
        async def _raise() -> BrokerOrder:
            raise BrokerNotSupportedError("TradingView sends orders inbound via webhook")

        return await self._execute("place_order", _raise)

    async def modify_order(self, order_id: str, request: ModifyOrderRequest) -> BrokerOrder:
        raise BrokerNotSupportedError("TradingView webhook adapter does not support modify_order")

    async def cancel_order(self, order_id: str) -> BrokerOrder:
        raise BrokerNotSupportedError("TradingView webhook adapter does not support cancel_order")
