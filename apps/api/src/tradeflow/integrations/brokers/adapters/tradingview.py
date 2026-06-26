"""TradingView webhook adapter — inbound signal integration."""

from __future__ import annotations

import hashlib
import hmac
import uuid
from collections import deque
from datetime import UTC, datetime
from decimal import Decimal

from tradeflow.integrations.brokers.base import BaseBrokerAdapter
from tradeflow.integrations.brokers.capabilities import BrokerCapabilities
from tradeflow.integrations.brokers.exceptions import BrokerConnectionError, BrokerNotSupportedError
from tradeflow.integrations.brokers.types import (
    BrokerAccount,
    BrokerCredentials,
    BrokerOrder,
    BrokerOrderSide,
    BrokerOrderStatus,
    BrokerOrderType,
    BrokerPosition,
    ModifyOrderRequest,
    PlaceOrderRequest,
    StreamHandler,
    StreamSubscription,
)


class TradingViewWebhookAdapter(BaseBrokerAdapter):
    """Receives TradingView alerts via webhook — outbound trading not supported."""

    def __init__(self, **kwargs: object) -> None:
        super().__init__(**kwargs)  # type: ignore[arg-type]
        self._webhook_secret: str | None = None
        self._orders: deque[BrokerOrder] = deque(maxlen=500)
        self._account_id = "tradingview-default"

    @property
    def broker_name(self) -> str:
        return "tradingview"

    @property
    def capabilities(self) -> BrokerCapabilities:
        return BrokerCapabilities(
            supports_rest=False,
            supports_websocket=True,
            supports_modify_order=False,
            supports_cancel_order=False,
            supports_flatten_position=False,
            supports_webhook_inbound=True,
            supports_stream_orders=True,
            supported_asset_classes=("signals",),
            notes="Inbound webhook signals only — use ingest_webhook()",
        )

    async def _connect_impl(self, credentials: BrokerCredentials) -> None:
        secret = credentials.data.get("webhook_secret")
        if not secret:
            raise BrokerConnectionError("TradingView adapter requires webhook_secret")
        self._webhook_secret = str(secret)
        self._account_id = str(credentials.data.get("account_id", "tradingview-default"))
        await self._connect_websocket("wss://tradingview.local/signals")

    async def _validate_connection_impl(self) -> None:
        if not self._webhook_secret:
            raise BrokerConnectionError("Webhook secret not configured")

    async def validate_webhook_signature(self, body: bytes, signature: str | None) -> bool:
        """Verify HMAC-SHA256 signature from TradingView alert webhook."""
        if not self._webhook_secret or not signature:
            return False
        expected = hmac.new(
            self._webhook_secret.encode(),
            body,
            hashlib.sha256,
        ).hexdigest()
        return hmac.compare_digest(expected, signature)

    async def ingest_webhook(self, payload: dict[str, object]) -> BrokerOrder:
        """Process inbound TradingView alert and emit order stream event."""
        action = str(payload.get("action", payload.get("side", "buy"))).lower()
        side = BrokerOrderSide.BUY if action in {"buy", "long"} else BrokerOrderSide.SELL
        symbol = str(payload.get("symbol", payload.get("ticker", "UNKNOWN")))
        quantity = Decimal(str(payload.get("quantity", payload.get("contracts", "1"))))
        order = BrokerOrder(
            id=str(uuid.uuid4()),
            account_id=self._account_id,
            symbol=symbol,
            side=side,
            order_type=BrokerOrderType.MARKET,
            quantity=quantity,
            price=None,
            status=BrokerOrderStatus.FILLED,
            filled_quantity=quantity,
            created_at=datetime.now(tz=UTC),
            metadata={"source": "tradingview", "payload": payload},
        )
        self._orders.appendleft(order)
        await self.websocket.publish({"type": "order", "order": order})
        return order

    async def fetch_accounts(self) -> list[BrokerAccount]:
        async def _fetch() -> list[BrokerAccount]:
            return [
                BrokerAccount(
                    id=self._account_id,
                    name="TradingView Signals",
                    currency="USD",
                    is_live=True,
                    metadata={"type": "webhook"},
                ),
            ]

        return await self._execute("fetch_accounts", _fetch)

    async def fetch_orders(self, account_id: str) -> list[BrokerOrder]:
        async def _fetch() -> list[BrokerOrder]:
            return list(self._orders)

        return await self._execute("fetch_orders", _fetch)

    async def fetch_positions(self, account_id: str) -> list[BrokerPosition]:
        async def _fetch() -> list[BrokerPosition]:
            return []

        return await self._execute("fetch_positions", _fetch)

    async def place_order(self, request: PlaceOrderRequest) -> BrokerOrder:
        raise BrokerNotSupportedError("TradingView sends orders inbound via webhook")

    async def modify_order(self, order_id: str, request: ModifyOrderRequest) -> BrokerOrder:
        raise BrokerNotSupportedError("TradingView webhook adapter does not support modify_order")

    async def cancel_order(self, order_id: str) -> BrokerOrder:
        raise BrokerNotSupportedError("TradingView webhook adapter does not support cancel_order")

    async def _stream_orders_impl(
        self,
        account_id: str,
        handler: StreamHandler,
    ) -> StreamSubscription:
        return await self.websocket.subscribe(f"orders:{account_id}", handler)
