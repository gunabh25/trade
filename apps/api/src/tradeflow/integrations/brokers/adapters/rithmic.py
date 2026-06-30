"""Rithmic adapter — R | Protocol architecture via sdk/rithmic_protocol.py."""

from __future__ import annotations

from tradeflow.integrations.brokers.base import BaseBrokerAdapter
from tradeflow.integrations.brokers.capabilities import BrokerCapabilities
from tradeflow.integrations.brokers.exceptions import BrokerNotSupportedError
from tradeflow.integrations.brokers.sdk.rithmic_protocol import (
    RithmicCredentials,
    RithmicProtocolClient,
)
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
    "Rithmic R | Protocol integration requires production SDK credentials. "
    "Connection architecture is wired; contact Rithmic for SDK access."
)


class RithmicBrokerAdapter(BaseBrokerAdapter):
    """Rithmic R Protocol API — protocol client architecture ready for SDK."""

    def __init__(self, **kwargs: object) -> None:
        super().__init__(**kwargs)  # type: ignore[arg-type]
        self._protocol: RithmicProtocolClient | None = None

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
        creds = RithmicCredentials.from_dict(credentials.data)
        self._protocol = RithmicProtocolClient(credentials=creds)
        await self._protocol.connect()

    async def _validate_connection_impl(self) -> None:
        if self._protocol is None:
            raise BrokerNotSupportedError(_RITHMIC_MSG)
        if not await self._protocol.validate_connection():
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
