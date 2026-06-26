"""Tradovate REST + OAuth adapter."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal
from typing import Any

from tradeflow.integrations.brokers.adapters.rest_base import RestBrokerAdapter
from tradeflow.integrations.brokers.capabilities import BrokerCapabilities
from tradeflow.integrations.brokers.exceptions import BrokerAuthError, BrokerConnectionError
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


class TradovateBrokerAdapter(RestBrokerAdapter):
    """Tradovate API — https://api.tradovate.com/"""

    required_credential_keys = ("username", "password")
    default_base_url = "https://live.tradovateapi.com/v1"
    websocket_url = "wss://live.tradovateapi.com/v1/websocket"

    @property
    def broker_name(self) -> str:
        return "tradovate"

    @property
    def capabilities(self) -> BrokerCapabilities:
        return BrokerCapabilities(
            supports_websocket=True,
            supports_token_refresh=True,
            supports_stream_market_data=True,
            supports_stream_orders=True,
            supports_stream_positions=True,
            max_orders_per_second=5.0,
            supported_asset_classes=("futures",),
        )

    def _build_http_client(self, credentials: BrokerCredentials, base_url: str) -> BrokerHttpClient:
        if credentials.data.get("demo"):
            base_url = "https://demo.tradovateapi.com/v1"
        pool = BrokerHttpPool(base_url=base_url)
        limiter = TokenBucketRateLimiter(rate_per_second=self.capabilities.max_orders_per_second)
        return BrokerHttpClient(
            broker_name=self.broker_name,
            pool=pool,
            rate_limiter=limiter,
            default_headers={"Content-Type": "application/json"},
        )

    async def _connect_impl(self, credentials: BrokerCredentials) -> None:
        await super()._connect_impl(credentials)
        await self._authenticate(credentials)

    async def _authenticate(self, credentials: BrokerCredentials) -> None:
        body = {
            "name": credentials.data["username"],
            "password": credentials.data["password"],
            "appId": credentials.data.get("app_id", "TradeFlow"),
            "appVersion": credentials.data.get("app_version", "1.0"),
            "deviceId": credentials.data.get("device_id", "tradeflow-server"),
            "cid": credentials.data.get("cid", 0),
            "sec": credentials.data.get("sec", ""),
        }
        data = await self._http_client().post("/auth/accesstokenrequest", json_body=body)
        token = data.get("accessToken")
        if not token:
            raise BrokerAuthError("Tradovate authentication failed — no access token returned")
        self._access_token = str(token)  # type: ignore[attr-defined]
        expiration = data.get("expirationTime")
        self._token_expires_at = (  # type: ignore[attr-defined]
            datetime.fromisoformat(str(expiration).replace("Z", "+00:00"))
            if expiration
            else datetime.now(tz=UTC) + timedelta(hours=1)
        )
        self._http_client()._default_headers["Authorization"] = f"Bearer {self._access_token}"

    async def _refresh_token_impl(self) -> None:
        if self._credentials is None:
            raise BrokerConnectionError("Not connected")
        data = await self._http_client().post(
            "/auth/renewaccesstoken",
            json_body={},
        )
        token = data.get("accessToken")
        if not token:
            await self._authenticate(self._credentials)
            return
        self._access_token = str(token)  # type: ignore[attr-defined]
        self._http_client()._default_headers["Authorization"] = f"Bearer {self._access_token}"

    async def _validate_connection_impl(self) -> None:
        await self._http_client().get("/auth/me")

    async def _fetch_accounts_impl(self) -> list[BrokerAccount]:
        data = await self._http_client().get("/account/list")
        rows = data if isinstance(data, list) else data.get("accounts", [])
        return [
            BrokerAccount(
                id=str(row.get("id", "")),
                name=str(row.get("name", f"Tradovate {row.get('id')}")),
                currency="USD",
                balance=self._decimal(row.get("cashBalance", "0")),
                equity=self._decimal(row.get("netLiq", row.get("cashBalance", "0"))),
                is_live=not bool(self._credentials and self._credentials.data.get("demo")),
                metadata=row,
            )
            for row in rows
        ]

    async def _fetch_orders_impl(self, account_id: str) -> list[BrokerOrder]:
        data = await self._http_client().get("/order/list")
        rows = data if isinstance(data, list) else []
        return [
            self._map_order(row, account_id)
            for row in rows
            if str(row.get("accountId", account_id)) == account_id
        ]

    async def _fetch_positions_impl(self, account_id: str) -> list[BrokerPosition]:
        data = await self._http_client().get("/position/list")
        rows = data if isinstance(data, list) else []
        positions: list[BrokerPosition] = []
        for row in rows:
            if str(row.get("accountId", account_id)) != account_id:
                continue
            qty = self._decimal(row.get("netPos", "0"))
            if qty == 0:
                continue
            positions.append(
                BrokerPosition(
                    id=str(row.get("id", row.get("contractId", ""))),
                    account_id=account_id,
                    symbol=str(row.get("contractName", row.get("symbol", ""))),
                    side=BrokerPositionSide.LONG if qty > 0 else BrokerPositionSide.SHORT,
                    quantity=abs(qty),
                    entry_price=self._decimal(row.get("avgPrice", "0")),
                    mark_price=self._decimal(row.get("markPrice", "0")),
                    unrealized_pnl=self._decimal(row.get("openPnL", "0")),
                    metadata=row,
                ),
            )
        return positions

    async def _place_order_impl(self, request: PlaceOrderRequest) -> BrokerOrder:
        body: dict[str, Any] = {
            "accountId": int(request.account_id),
            "action": "Buy" if request.side == BrokerOrderSide.BUY else "Sell",
            "symbol": request.symbol,
            "orderQty": float(request.quantity),
            "orderType": "Market" if request.order_type == BrokerOrderType.MARKET else "Limit",
        }
        if request.price is not None:
            body["price"] = float(request.price)
        data = await self._http_client().post("/order/placeorder", json_body=body)
        order_id = str(data.get("orderId", data.get("id", "")))
        return BrokerOrder(
            id=order_id,
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
        body: dict[str, Any] = {"orderId": int(order_id)}
        if request.quantity is not None:
            body["orderQty"] = float(request.quantity)
        if request.price is not None:
            body["price"] = float(request.price)
        data = await self._http_client().post("/order/modifyorder", json_body=body)
        return BrokerOrder(
            id=order_id,
            account_id=str(self._account_id or ""),
            symbol="",
            side=BrokerOrderSide.BUY,
            order_type=BrokerOrderType.LIMIT,
            quantity=request.quantity or Decimal("0"),
            price=request.price,
            status=BrokerOrderStatus.OPEN,
            metadata=data,
        )

    async def _cancel_order_impl(self, order_id: str) -> BrokerOrder:
        data = await self._http_client().post(
            "/order/cancelorder",
            json_body={"orderId": int(order_id)},
        )
        return BrokerOrder(
            id=order_id,
            account_id=str(self._account_id or ""),
            symbol="",
            side=BrokerOrderSide.BUY,
            order_type=BrokerOrderType.MARKET,
            quantity=Decimal("0"),
            price=None,
            status=BrokerOrderStatus.CANCELED,
            metadata=data,
        )

    def _map_order(self, row: dict[str, Any], account_id: str) -> BrokerOrder:
        return BrokerOrder(
            id=str(row.get("id", row.get("orderId", ""))),
            account_id=account_id,
            symbol=str(row.get("symbol", "")),
            side=BrokerOrderSide.BUY if row.get("action") == "Buy" else BrokerOrderSide.SELL,
            order_type=BrokerOrderType.MARKET,
            quantity=self._decimal(row.get("orderQty", "0")),
            price=self._decimal(row.get("price")) if row.get("price") else None,
            status=BrokerOrderStatus.OPEN,
            metadata=row,
        )
