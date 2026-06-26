"""Binance Spot REST adapter — production signed API integration."""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from typing import Any

from tradeflow.integrations.brokers.adapters._signing import binance_sign_params
from tradeflow.integrations.brokers.adapters.rest_base import RestBrokerAdapter
from tradeflow.integrations.brokers.capabilities import BrokerCapabilities
from tradeflow.integrations.brokers.http_client import BrokerHttpClient
from tradeflow.integrations.brokers.pool import BrokerHttpPool
from tradeflow.integrations.brokers.rate_limit import TokenBucketRateLimiter
from tradeflow.integrations.brokers.types import (
    BrokerAccount,
    BrokerCredentials,
    BrokerOrder,
    BrokerOrderSide,
    BrokerOrderStatus,
    BrokerOrderType,
    BrokerPosition,
    BrokerPositionSide,
    ModifyOrderRequest,
    PlaceOrderRequest,
)

_SIDE_MAP = {BrokerOrderSide.BUY: "BUY", BrokerOrderSide.SELL: "SELL"}
_TYPE_MAP = {
    BrokerOrderType.MARKET: "MARKET",
    BrokerOrderType.LIMIT: "LIMIT",
    BrokerOrderType.STOP: "STOP_LOSS",
    BrokerOrderType.STOP_LIMIT: "STOP_LOSS_LIMIT",
}
_STATUS_MAP = {
    "NEW": BrokerOrderStatus.OPEN,
    "PARTIALLY_FILLED": BrokerOrderStatus.PARTIAL,
    "FILLED": BrokerOrderStatus.FILLED,
    "CANCELED": BrokerOrderStatus.CANCELED,
    "REJECTED": BrokerOrderStatus.REJECTED,
    "EXPIRED": BrokerOrderStatus.CANCELED,
}


class BinanceBrokerAdapter(RestBrokerAdapter):
    """Binance Spot API — https://binance-docs.github.io/apidocs/spot/en/"""

    required_credential_keys = ("api_key", "api_secret")
    default_base_url = "https://api.binance.com"
    websocket_url = "wss://stream.binance.com:9443/ws"

    @property
    def broker_name(self) -> str:
        return "binance"

    @property
    def capabilities(self) -> BrokerCapabilities:
        return BrokerCapabilities(
            supports_websocket=True,
            supports_stop_orders=True,
            supports_stream_market_data=True,
            supports_stream_orders=True,
            max_orders_per_second=10.0,
            supported_asset_classes=("crypto",),
        )

    def _build_http_client(self, credentials: BrokerCredentials, base_url: str) -> BrokerHttpClient:
        api_key = str(credentials.data["api_key"])
        api_secret = str(credentials.data["api_secret"])
        if credentials.data.get("testnet"):
            base_url = "https://testnet.binance.vision"
        pool = BrokerHttpPool(base_url=base_url)
        limiter = TokenBucketRateLimiter(rate_per_second=self.capabilities.max_orders_per_second)

        async def _signed_get(path: str, params: dict[str, Any] | None = None) -> Any:
            signed = binance_sign_params(params or {}, api_secret)
            return await BrokerHttpClient(
                broker_name=self.broker_name,
                pool=pool,
                rate_limiter=limiter,
                default_headers={"X-MBX-APIKEY": api_key},
            ).get(path, params=signed)

        self._signed_get = _signed_get  # type: ignore[attr-defined]
        self._api_secret = api_secret  # type: ignore[attr-defined]
        self._api_key = api_key  # type: ignore[attr-defined]
        return BrokerHttpClient(
            broker_name=self.broker_name,
            pool=pool,
            rate_limiter=limiter,
            default_headers={"X-MBX-APIKEY": api_key},
        )

    async def _signed_request(
        self,
        method: str,
        path: str,
        params: dict[str, Any] | None = None,
    ) -> Any:
        signed = binance_sign_params(params or {}, self._api_secret)  # type: ignore[attr-defined]
        client = self._http_client()
        if method == "GET":
            return await client.get(path, params=signed)
        if method == "POST":
            return await client.post(path, params=signed)
        if method == "DELETE":
            return await client.delete(path, params=signed)
        msg = f"Unsupported method {method}"
        raise ValueError(msg)

    async def _validate_connection_impl(self) -> None:
        await self._signed_request("GET", "/api/v3/ping")

    async def _fetch_accounts_impl(self) -> list[BrokerAccount]:
        data = await self._signed_request("GET", "/api/v3/account")
        balances = data.get("balances", [])
        total_usdt = sum(
            self._decimal(b.get("free", "0")) + self._decimal(b.get("locked", "0"))
            for b in balances
            if self._decimal(b.get("free", "0")) + self._decimal(b.get("locked", "0")) > 0
        )
        account_id = str(self._account_id or data.get("accountType", "spot"))
        return [
            BrokerAccount(
                id=account_id,
                name=f"Binance {account_id}",
                currency="USDT",
                balance=total_usdt,
                equity=total_usdt,
                is_live=not bool(self._credentials and self._credentials.data.get("testnet")),
                metadata={"can_trade": data.get("canTrade"), "balances": balances[:20]},
            ),
        ]

    def _default_symbol(self) -> str:
        if self._credentials:
            return str(self._credentials.data.get("default_symbol", "BTCUSDT"))
        return "BTCUSDT"

    async def _fetch_orders_impl(self, account_id: str) -> list[BrokerOrder]:
        symbol = self._default_symbol()
        data = await self._signed_request("GET", "/api/v3/openOrders", {"symbol": symbol})
        return [self._map_order(row, account_id) for row in data]

    async def _fetch_positions_impl(self, account_id: str) -> list[BrokerPosition]:
        data = await self._signed_request("GET", "/api/v3/account")
        positions: list[BrokerPosition] = []
        for bal in data.get("balances", []):
            qty = self._decimal(bal.get("free", "0")) + self._decimal(bal.get("locked", "0"))
            if qty <= 0 or bal.get("asset") in {"USDT", "USD", "BUSD"}:
                continue
            asset = str(bal["asset"])
            positions.append(
                BrokerPosition(
                    id=f"{account_id}:{asset}",
                    account_id=account_id,
                    symbol=f"{asset}USDT",
                    side=BrokerPositionSide.LONG,
                    quantity=qty,
                    entry_price=Decimal("0"),
                    mark_price=Decimal("0"),
                    metadata={"asset": asset},
                ),
            )
        return positions

    async def _place_order_impl(self, request: PlaceOrderRequest) -> BrokerOrder:
        params: dict[str, Any] = {
            "symbol": request.symbol,
            "side": _SIDE_MAP[request.side],
            "type": _TYPE_MAP.get(request.order_type, "MARKET"),
            "quantity": str(request.quantity),
        }
        if request.order_type == BrokerOrderType.LIMIT and request.price is not None:
            params["price"] = str(request.price)
            params["timeInForce"] = "GTC"
        if request.metadata.get("reduce_only"):
            params["side"] = "SELL" if params["side"] == "BUY" else "BUY"
        data = await self._signed_request("POST", "/api/v3/order", params)
        return self._map_order(data, request.account_id)

    async def _modify_order_impl(self, order_id: str, request: ModifyOrderRequest) -> BrokerOrder:
        symbol = self._default_symbol()
        params: dict[str, Any] = {"symbol": symbol, "orderId": order_id}
        if request.quantity is not None:
            params["quantity"] = str(request.quantity)
        if request.price is not None:
            params["price"] = str(request.price)
        data = await self._signed_request("POST", "/api/v3/order/cancelReplace", params)
        return self._map_order(data.get("newOrderResponse", data), symbol)

    async def _cancel_order_impl(self, order_id: str) -> BrokerOrder:
        symbol = self._default_symbol()
        data = await self._signed_request(
            "DELETE",
            "/api/v3/order",
            {"symbol": symbol, "orderId": order_id},
        )
        return self._map_order(data, symbol)

    def _map_order(self, row: dict[str, Any], account_id: str) -> BrokerOrder:
        status = _STATUS_MAP.get(str(row.get("status", "NEW")), BrokerOrderStatus.OPEN)
        return BrokerOrder(
            id=str(row.get("orderId", row.get("clientOrderId", ""))),
            account_id=account_id,
            symbol=str(row.get("symbol", "")),
            side=BrokerOrderSide.BUY if row.get("side") == "BUY" else BrokerOrderSide.SELL,
            order_type=BrokerOrderType.MARKET,
            quantity=self._decimal(row.get("origQty")),
            price=self._decimal(row.get("price")) if row.get("price") else None,
            status=status,
            filled_quantity=self._decimal(row.get("executedQty")),
            created_at=datetime.fromtimestamp(row["time"] / 1000, tz=UTC)
            if row.get("time")
            else None,
            metadata=row,
        )
