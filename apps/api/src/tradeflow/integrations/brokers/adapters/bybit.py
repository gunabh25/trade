"""Bybit V5 REST adapter — unified trading account."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any

from tradeflow.integrations.brokers.adapters._signing import bybit_sign_headers
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

_STATUS_MAP = {
    "New": BrokerOrderStatus.OPEN,
    "PartiallyFilled": BrokerOrderStatus.PARTIAL,
    "Filled": BrokerOrderStatus.FILLED,
    "Cancelled": BrokerOrderStatus.CANCELED,
    "Rejected": BrokerOrderStatus.REJECTED,
}


class BybitBrokerAdapter(RestBrokerAdapter):
    """Bybit V5 API — https://bybit-exchange.github.io/docs/v5/intro"""

    required_credential_keys = ("api_key", "api_secret")
    default_base_url = "https://api.bybit.com"
    websocket_url = "wss://stream.bybit.com/v5/public/linear"

    @property
    def broker_name(self) -> str:
        return "bybit"

    @property
    def capabilities(self) -> BrokerCapabilities:
        return BrokerCapabilities(
            supports_websocket=True,
            supports_stop_orders=True,
            supports_stream_market_data=True,
            supports_stream_orders=True,
            supports_stream_positions=True,
            max_orders_per_second=10.0,
            supported_asset_classes=("crypto", "futures"),
        )

    def _build_http_client(self, credentials: BrokerCredentials, base_url: str) -> BrokerHttpClient:
        self._api_key = str(credentials.data["api_key"])  # type: ignore[attr-defined]
        self._api_secret = str(credentials.data["api_secret"])  # type: ignore[attr-defined]
        if credentials.data.get("testnet"):
            base_url = "https://api-testnet.bybit.com"
        pool = BrokerHttpPool(base_url=base_url)
        limiter = TokenBucketRateLimiter(rate_per_second=self.capabilities.max_orders_per_second)
        return BrokerHttpClient(
            broker_name=self.broker_name,
            pool=pool,
            rate_limiter=limiter,
        )

    async def _signed_get(self, path: str, params: dict[str, Any] | None = None) -> Any:
        query = json.dumps(params or {}, separators=(",", ":"))
        headers = bybit_sign_headers(
            self._api_key,  # type: ignore[attr-defined]
            self._api_secret,  # type: ignore[attr-defined]
            payload=query,
        )
        client = self._http_client()
        data = await client.request("GET", path, params=params, headers=headers)
        self._ensure_ok(data)
        return data.get("result", data)

    async def _signed_post(self, path: str, body: dict[str, Any]) -> Any:
        payload = json.dumps(body, separators=(",", ":"))
        headers = bybit_sign_headers(
            self._api_key,  # type: ignore[attr-defined]
            self._api_secret,  # type: ignore[attr-defined]
            payload=payload,
        )
        client = self._http_client()
        data = await client.request("POST", path, json_body=body, headers=headers)
        self._ensure_ok(data)
        return data.get("result", data)

    @staticmethod
    def _ensure_ok(data: dict[str, Any]) -> None:
        if int(data.get("retCode", 0)) != 0:
            msg = data.get("retMsg", "Bybit API error")
            raise ValueError(msg)

    async def _validate_connection_impl(self) -> None:
        await self._signed_get("/v5/market/time")

    async def _fetch_accounts_impl(self) -> list[BrokerAccount]:
        data = await self._signed_get("/v5/account/wallet-balance", {"accountType": "UNIFIED"})
        accounts: list[BrokerAccount] = []
        for row in data.get("list", []):
            total = self._decimal(row.get("totalEquity"))
            account_id = str(row.get("accountId") or self._account_id or "unified")
            accounts.append(
                BrokerAccount(
                    id=account_id,
                    name=f"Bybit {account_id}",
                    currency="USDT",
                    balance=total,
                    equity=total,
                    is_live=True,
                    metadata=row,
                ),
            )
        return accounts

    async def _fetch_orders_impl(self, account_id: str) -> list[BrokerOrder]:
        data = await self._signed_get(
            "/v5/order/realtime",
            {"category": "linear", "settleCoin": "USDT"},
        )
        return [self._map_order(row, account_id) for row in data.get("list", [])]

    async def _fetch_positions_impl(self, account_id: str) -> list[BrokerPosition]:
        data = await self._signed_get(
            "/v5/position/list",
            {"category": "linear", "settleCoin": "USDT"},
        )
        positions: list[BrokerPosition] = []
        for row in data.get("list", []):
            size = self._decimal(row.get("size"))
            if size <= 0:
                continue
            side = BrokerPositionSide.LONG if row.get("side") == "Buy" else BrokerPositionSide.SHORT
            positions.append(
                BrokerPosition(
                    id=str(row.get("positionIdx", row.get("symbol"))),
                    account_id=account_id,
                    symbol=str(row.get("symbol", "")),
                    side=side,
                    quantity=size,
                    entry_price=self._decimal(row.get("avgPrice")),
                    mark_price=self._decimal(row.get("markPrice")),
                    unrealized_pnl=self._decimal(row.get("unrealisedPnl")),
                    metadata=row,
                ),
            )
        return positions

    async def _place_order_impl(self, request: PlaceOrderRequest) -> BrokerOrder:
        body: dict[str, Any] = {
            "category": "linear",
            "symbol": request.symbol,
            "side": "Buy" if request.side == BrokerOrderSide.BUY else "Sell",
            "orderType": "Market" if request.order_type == BrokerOrderType.MARKET else "Limit",
            "qty": str(request.quantity),
        }
        if request.price is not None:
            body["price"] = str(request.price)
        if request.metadata.get("reduce_only"):
            body["reduceOnly"] = True
        data = await self._signed_post("/v5/order/create", body)
        return BrokerOrder(
            id=str(data.get("orderId", "")),
            account_id=request.account_id,
            symbol=request.symbol,
            side=request.side,
            order_type=request.order_type,
            quantity=request.quantity,
            price=request.price,
            status=BrokerOrderStatus.OPEN,
            metadata=data,
        )

    async def _modify_order_impl(self, order_id: str, request: ModifyOrderRequest) -> BrokerOrder:
        body: dict[str, Any] = {"category": "linear", "orderId": order_id}
        if request.quantity is not None:
            body["qty"] = str(request.quantity)
        if request.price is not None:
            body["price"] = str(request.price)
        data = await self._signed_post("/v5/order/amend", body)
        return BrokerOrder(
            id=order_id,
            account_id=str(self._account_id or ""),
            symbol=str(data.get("symbol", "")),
            side=BrokerOrderSide.BUY,
            order_type=BrokerOrderType.LIMIT,
            quantity=request.quantity or Decimal("0"),
            price=request.price,
            status=BrokerOrderStatus.OPEN,
            metadata=data,
        )

    async def _cancel_order_impl(self, order_id: str) -> BrokerOrder:
        data = await self._signed_post(
            "/v5/order/cancel",
            {"category": "linear", "orderId": order_id},
        )
        return BrokerOrder(
            id=order_id,
            account_id=str(self._account_id or ""),
            symbol=str(data.get("symbol", "")),
            side=BrokerOrderSide.BUY,
            order_type=BrokerOrderType.MARKET,
            quantity=Decimal("0"),
            price=None,
            status=BrokerOrderStatus.CANCELED,
            metadata=data,
        )

    def _map_order(self, row: dict[str, Any], account_id: str) -> BrokerOrder:
        status = _STATUS_MAP.get(str(row.get("orderStatus", "New")), BrokerOrderStatus.OPEN)
        return BrokerOrder(
            id=str(row.get("orderId", "")),
            account_id=account_id,
            symbol=str(row.get("symbol", "")),
            side=BrokerOrderSide.BUY if row.get("side") == "Buy" else BrokerOrderSide.SELL,
            order_type=BrokerOrderType.MARKET,
            quantity=self._decimal(row.get("qty")),
            price=self._decimal(row.get("price")) if row.get("price") else None,
            status=status,
            filled_quantity=self._decimal(row.get("cumExecQty")),
            created_at=datetime.fromtimestamp(int(row["createdTime"]) / 1000, tz=UTC)
            if row.get("createdTime")
            else None,
            metadata=row,
        )
