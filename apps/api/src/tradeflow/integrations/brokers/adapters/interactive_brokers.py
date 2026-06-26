"""Interactive Brokers Client Portal Web API adapter."""

from __future__ import annotations

from decimal import Decimal
from typing import Any

from tradeflow.integrations.brokers.adapters.rest_base import RestBrokerAdapter
from tradeflow.integrations.brokers.capabilities import BrokerCapabilities
from tradeflow.integrations.brokers.exceptions import BrokerConnectionError
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


class InteractiveBrokersAdapter(RestBrokerAdapter):
    """IB Client Portal API — requires IB Gateway / TWS on localhost:5000."""

    required_credential_keys = ("account_id",)
    default_base_url = "https://localhost:5000/v1/api"
    websocket_url = "wss://localhost:5000/v1/api/ws"

    @property
    def broker_name(self) -> str:
        return "interactive_brokers"

    @property
    def capabilities(self) -> BrokerCapabilities:
        return BrokerCapabilities(
            supports_websocket=True,
            supports_stop_orders=True,
            supports_stream_market_data=True,
            supports_stream_orders=True,
            supports_stream_positions=True,
            max_orders_per_second=5.0,
            supported_asset_classes=("equity", "options", "futures", "forex"),
            notes="Requires IB Gateway with Client Portal API enabled",
        )

    def _build_http_client(self, credentials: BrokerCredentials, base_url: str) -> BrokerHttpClient:
        base_url = str(credentials.data.get("base_url", base_url))
        pool = BrokerHttpPool(base_url=base_url, timeout_seconds=60.0)
        limiter = TokenBucketRateLimiter(rate_per_second=self.capabilities.max_orders_per_second)
        return BrokerHttpClient(
            broker_name=self.broker_name,
            pool=pool,
            rate_limiter=limiter,
            default_headers={"Content-Type": "application/json"},
        )

    async def _connect_impl(self, credentials: BrokerCredentials) -> None:
        await super()._connect_impl(credentials)
        if credentials.data.get("username"):
            try:
                await self._http_client().post(
                    "/iserver/auth/ssodh/init",
                    json_body={"publish": True, "compete": True},
                )
            except Exception as exc:
                raise BrokerConnectionError(
                    "IB Gateway authentication failed — ensure Client Portal is running",
                ) from exc

    async def _validate_connection_impl(self) -> None:
        await self._http_client().get("/tickle")

    async def _fetch_accounts_impl(self) -> list[BrokerAccount]:
        data = await self._http_client().get("/portfolio/accounts")
        accounts: list[BrokerAccount] = []
        for row in data if isinstance(data, list) else data.get("accounts", []):
            account_id = str(row.get("accountId") or row.get("id") or self._account_id)
            accounts.append(
                BrokerAccount(
                    id=account_id,
                    name=str(row.get("accountTitle", f"IB {account_id}")),
                    currency=str(row.get("currency", "USD")),
                    balance=self._decimal(row.get("balance", "0")),
                    equity=self._decimal(row.get("equity", row.get("balance", "0"))),
                    is_live=True,
                    metadata=row if isinstance(row, dict) else {"raw": row},
                ),
            )
        if not accounts and self._account_id:
            accounts.append(
                BrokerAccount(
                    id=str(self._account_id),
                    name=f"IB {self._account_id}",
                    currency="USD",
                    is_live=True,
                ),
            )
        return accounts

    async def _fetch_orders_impl(self, account_id: str) -> list[BrokerOrder]:
        data = await self._http_client().get("/iserver/account/orders")
        orders: list[BrokerOrder] = []
        for row in data.get("orders", []) if isinstance(data, dict) else data:
            if str(row.get("acct", account_id)) != account_id:
                continue
            orders.append(self._map_order(row, account_id))
        return orders

    async def _fetch_positions_impl(self, account_id: str) -> list[BrokerPosition]:
        data = await self._http_client().get(f"/portfolio/{account_id}/positions/0")
        positions: list[BrokerPosition] = []
        for row in data if isinstance(data, list) else []:
            qty = self._decimal(row.get("position", row.get("quantity", "0")))
            if qty == 0:
                continue
            positions.append(
                BrokerPosition(
                    id=str(row.get("conid", row.get("contractDesc", ""))),
                    account_id=account_id,
                    symbol=str(row.get("contractDesc", row.get("ticker", ""))),
                    side=BrokerPositionSide.LONG if qty > 0 else BrokerPositionSide.SHORT,
                    quantity=abs(qty),
                    entry_price=self._decimal(row.get("avgCost", "0")),
                    mark_price=self._decimal(row.get("mktPrice", "0")),
                    unrealized_pnl=self._decimal(row.get("unrealizedPnl", "0")),
                    metadata=row,
                ),
            )
        return positions

    async def _place_order_impl(self, request: PlaceOrderRequest) -> BrokerOrder:
        conid = request.metadata.get("conid") or request.symbol
        body = {
            "orders": [
                {
                    "conid": int(conid) if str(conid).isdigit() else conid,
                    "orderType": "MKT" if request.order_type == BrokerOrderType.MARKET else "LMT",
                    "side": "BUY" if request.side == BrokerOrderSide.BUY else "SELL",
                    "quantity": float(request.quantity),
                    "tif": "DAY",
                },
            ],
        }
        if request.price is not None:
            body["orders"][0]["price"] = float(request.price)
        data = await self._http_client().post(
            f"/iserver/account/{request.account_id}/orders",
            json_body=body,
        )
        order_id = str(data[0].get("order_id", "")) if isinstance(data, list) and data else ""
        return BrokerOrder(
            id=order_id,
            account_id=request.account_id,
            symbol=request.symbol,
            side=request.side,
            order_type=request.order_type,
            quantity=request.quantity,
            price=request.price,
            status=BrokerOrderStatus.OPEN,
            metadata={"response": data},
        )

    async def _modify_order_impl(self, order_id: str, request: ModifyOrderRequest) -> BrokerOrder:
        account_id = str(self._account_id or "")
        body: dict[str, Any] = {"orderId": order_id}
        if request.quantity is not None:
            body["quantity"] = float(request.quantity)
        if request.price is not None:
            body["price"] = float(request.price)
        data = await self._http_client().post(
            f"/iserver/account/{account_id}/order/{order_id}",
            json_body=body,
        )
        return BrokerOrder(
            id=order_id,
            account_id=account_id,
            symbol="",
            side=BrokerOrderSide.BUY,
            order_type=BrokerOrderType.LIMIT,
            quantity=request.quantity or Decimal("0"),
            price=request.price,
            status=BrokerOrderStatus.OPEN,
            metadata=data,
        )

    async def _cancel_order_impl(self, order_id: str) -> BrokerOrder:
        account_id = str(self._account_id or "")
        await self._http_client().delete(
            f"/iserver/account/{account_id}/order/{order_id}",
        )
        return BrokerOrder(
            id=order_id,
            account_id=account_id,
            symbol="",
            side=BrokerOrderSide.BUY,
            order_type=BrokerOrderType.MARKET,
            quantity=Decimal("0"),
            price=None,
            status=BrokerOrderStatus.CANCELED,
        )

    def _map_order(self, row: dict[str, Any], account_id: str) -> BrokerOrder:
        side_str = str(row.get("side", "BUY")).upper()
        return BrokerOrder(
            id=str(row.get("orderId", row.get("order_id", ""))),
            account_id=account_id,
            symbol=str(row.get("ticker", row.get("contractDesc", ""))),
            side=BrokerOrderSide.BUY if side_str == "BUY" else BrokerOrderSide.SELL,
            order_type=BrokerOrderType.MARKET,
            quantity=self._decimal(row.get("totalSize", row.get("quantity", "0"))),
            price=self._decimal(row.get("price")) if row.get("price") else None,
            status=BrokerOrderStatus.OPEN,
            metadata=row,
        )
