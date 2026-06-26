"""OANDA v20 REST adapter."""

from __future__ import annotations

from decimal import Decimal
from typing import Any

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


class OandaBrokerAdapter(RestBrokerAdapter):
    """OANDA v20 REST — https://developer.oanda.com/rest-live-v20/introduction/"""

    required_credential_keys = ("api_key", "account_id")
    default_base_url = "https://api-fxtrade.oanda.com"
    websocket_url = None

    @property
    def broker_name(self) -> str:
        return "oanda"

    @property
    def capabilities(self) -> BrokerCapabilities:
        return BrokerCapabilities(
            supports_stop_orders=True,
            supports_stream_market_data=False,
            max_orders_per_second=5.0,
            supported_asset_classes=("forex", "cfd"),
        )

    def _build_http_client(self, credentials: BrokerCredentials, base_url: str) -> BrokerHttpClient:
        if credentials.data.get("practice"):
            base_url = "https://api-fxpractice.oanda.com"
        api_key = str(credentials.data["api_key"])
        pool = BrokerHttpPool(base_url=base_url)
        limiter = TokenBucketRateLimiter(rate_per_second=self.capabilities.max_orders_per_second)
        return BrokerHttpClient(
            broker_name=self.broker_name,
            pool=pool,
            rate_limiter=limiter,
            default_headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
        )

    def _account_path(self, account_id: str) -> str:
        return f"/v3/accounts/{account_id}"

    async def _validate_connection_impl(self) -> None:
        account_id = str(self._account_id or self._credentials.data.get("account_id"))  # type: ignore[union-attr]
        await self._http_client().get(self._account_path(account_id))

    async def _fetch_accounts_impl(self) -> list[BrokerAccount]:
        account_id = str(self._account_id or self._credentials.data.get("account_id"))  # type: ignore[union-attr]
        data = await self._http_client().get(self._account_path(account_id))
        acct = data.get("account", data)
        balance = self._decimal(acct.get("balance"))
        return [
            BrokerAccount(
                id=account_id,
                name=str(acct.get("alias", f"OANDA {account_id}")),
                currency=str(acct.get("currency", "USD")),
                balance=balance,
                equity=self._decimal(acct.get("NAV", balance)),
                is_live=not bool(self._credentials and self._credentials.data.get("practice")),
                metadata=acct,
            ),
        ]

    async def _fetch_orders_impl(self, account_id: str) -> list[BrokerOrder]:
        data = await self._http_client().get(f"{self._account_path(account_id)}/pendingOrders")
        return [self._map_order(row, account_id) for row in data.get("orders", [])]

    async def _fetch_positions_impl(self, account_id: str) -> list[BrokerPosition]:
        data = await self._http_client().get(f"{self._account_path(account_id)}/openPositions")
        positions: list[BrokerPosition] = []
        for row in data.get("positions", []):
            long_units = self._decimal(row.get("long", {}).get("units", "0"))
            short_units = self._decimal(row.get("short", {}).get("units", "0"))
            if long_units > 0:
                positions.append(self._map_position(row, account_id, long_units, "long"))
            if short_units < 0:
                positions.append(
                    self._map_position(row, account_id, abs(short_units), "short"),
                )
        return positions

    async def _place_order_impl(self, request: PlaceOrderRequest) -> BrokerOrder:
        order_body: dict[str, Any] = {
            "order": {
                "instrument": request.symbol,
                "units": str(int(request.quantity))
                if request.side == BrokerOrderSide.BUY
                else str(-int(request.quantity)),
                "type": "MARKET" if request.order_type == BrokerOrderType.MARKET else "LIMIT",
            },
        }
        if request.price is not None:
            order_body["order"]["price"] = str(request.price)
        data = await self._http_client().post(
            f"{self._account_path(request.account_id)}/orders",
            json_body=order_body,
        )
        fill = data.get("orderFillTransaction") or data.get("orderCreateTransaction") or data
        return self._map_order(fill, request.account_id)

    async def _modify_order_impl(self, order_id: str, request: ModifyOrderRequest) -> BrokerOrder:
        account_id = str(self._account_id or "")
        body: dict[str, Any] = {}
        if request.quantity is not None:
            body["units"] = str(int(request.quantity))
        if request.price is not None:
            body["price"] = str(request.price)
        data = await self._http_client().put(
            f"{self._account_path(account_id)}/orders/{order_id}",
            json_body=body,
        )
        return self._map_order(data.get("order", data), account_id)

    async def _cancel_order_impl(self, order_id: str) -> BrokerOrder:
        account_id = str(self._account_id or "")
        data = await self._http_client().put(
            f"{self._account_path(account_id)}/orders/{order_id}/cancel",
            json_body={},
        )
        order = data.get("orderCancelTransaction", data)
        return BrokerOrder(
            id=order_id,
            account_id=account_id,
            symbol=str(order.get("instrument", "")),
            side=BrokerOrderSide.BUY,
            order_type=BrokerOrderType.MARKET,
            quantity=Decimal("0"),
            price=None,
            status=BrokerOrderStatus.CANCELED,
            metadata=order,
        )

    def _map_order(self, row: dict[str, Any], account_id: str) -> BrokerOrder:
        units = self._decimal(row.get("units", row.get("initialUnits", "0")))
        return BrokerOrder(
            id=str(row.get("id", row.get("orderID", ""))),
            account_id=account_id,
            symbol=str(row.get("instrument", "")),
            side=BrokerOrderSide.BUY if units >= 0 else BrokerOrderSide.SELL,
            order_type=BrokerOrderType.MARKET,
            quantity=abs(units),
            price=self._decimal(row.get("price")) if row.get("price") else None,
            status=BrokerOrderStatus.OPEN,
            metadata=row,
        )

    def _map_position(
        self,
        row: dict[str, Any],
        account_id: str,
        qty: Decimal,
        side: str,
    ) -> BrokerPosition:
        instrument = str(row.get("instrument", ""))
        return BrokerPosition(
            id=f"{account_id}:{instrument}",
            account_id=account_id,
            symbol=instrument,
            side=BrokerPositionSide.LONG if side == "long" else BrokerPositionSide.SHORT,
            quantity=qty,
            entry_price=self._decimal(row.get("averagePrice", "0")),
            mark_price=self._decimal(row.get("currentPrice", "0")),
            unrealized_pnl=self._decimal(row.get("unrealizedPL", "0")),
            metadata=row,
        )
