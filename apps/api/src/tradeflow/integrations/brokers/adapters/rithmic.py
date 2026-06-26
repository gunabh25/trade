"""Rithmic adapter — interface design pending production credentials."""

from __future__ import annotations

from tradeflow.integrations.brokers.base import BaseBrokerAdapter
from tradeflow.integrations.brokers.capabilities import BrokerCapabilities
from tradeflow.integrations.brokers.exceptions import BrokerConnectionError, BrokerNotSupportedError
from tradeflow.integrations.brokers.types import (
    BrokerAccount,
    BrokerCredentials,
    BrokerOrder,
    BrokerPosition,
    ModifyOrderRequest,
    PlaceOrderRequest,
    StreamHandler,
    StreamSubscription,
)

_RITHMIC_MSG = (
    "Rithmic R | Protocol API integration requires production credentials "
    "(user, password, system_name, gateway). Contact Rithmic for SDK access."
)


class RithmicBrokerAdapter(BaseBrokerAdapter):
    """Rithmic R Protocol API — interface stub until credentials are provisioned."""

    @property
    def broker_name(self) -> str:
        return "rithmic"

    @property
    def capabilities(self) -> BrokerCapabilities:
        return BrokerCapabilities(
            supports_rest=False,
            supports_websocket=True,
            supports_stream_market_data=True,
            supports_stream_orders=True,
            supports_stream_positions=True,
            supports_token_refresh=False,
            max_orders_per_second=20.0,
            supported_asset_classes=("futures",),
            notes=_RITHMIC_MSG,
        )

    async def _connect_impl(self, credentials: BrokerCredentials) -> None:
        required = ("username", "password", "system_name", "gateway")
        missing = [k for k in required if not credentials.data.get(k)]
        if missing:
            msg = (
                f"Rithmic requires credentials: {', '.join(required)}. "
                f"Missing: {', '.join(missing)}"
            )
            raise BrokerConnectionError(msg)
        raise BrokerNotSupportedError(_RITHMIC_MSG)

    async def _validate_connection_impl(self) -> None:
        raise BrokerNotSupportedError(_RITHMIC_MSG)

    async def fetch_accounts(self) -> list[BrokerAccount]:
        raise BrokerNotSupportedError(_RITHMIC_MSG)

    async def fetch_orders(self, account_id: str) -> list[BrokerOrder]:
        raise BrokerNotSupportedError(_RITHMIC_MSG)

    async def fetch_positions(self, account_id: str) -> list[BrokerPosition]:
        raise BrokerNotSupportedError(_RITHMIC_MSG)

    async def place_order(self, request: PlaceOrderRequest) -> BrokerOrder:
        raise BrokerNotSupportedError(_RITHMIC_MSG)

    async def modify_order(self, order_id: str, request: ModifyOrderRequest) -> BrokerOrder:
        raise BrokerNotSupportedError(_RITHMIC_MSG)

    async def cancel_order(self, order_id: str) -> BrokerOrder:
        raise BrokerNotSupportedError(_RITHMIC_MSG)

    async def flatten_position(self, account_id: str, symbol: str) -> BrokerOrder:
        raise BrokerNotSupportedError(_RITHMIC_MSG)

    async def stream_market_data(
        self,
        symbols: list[str],
        handler: StreamHandler,
    ) -> StreamSubscription:
        raise BrokerNotSupportedError(_RITHMIC_MSG)

    async def stream_orders(self, account_id: str, handler: StreamHandler) -> StreamSubscription:
        raise BrokerNotSupportedError(_RITHMIC_MSG)

    async def stream_positions(self, account_id: str, handler: StreamHandler) -> StreamSubscription:
        raise BrokerNotSupportedError(_RITHMIC_MSG)
