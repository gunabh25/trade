"""Paper trading adapter — full in-memory implementation for development."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from decimal import Decimal

from tradeflow.integrations.brokers.base import BaseBrokerAdapter
from tradeflow.integrations.brokers.capabilities import BrokerCapabilities
from tradeflow.integrations.brokers.retry import RetryPolicy
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
    StreamHandler,
    StreamSubscription,
)


class PaperBrokerAdapter(BaseBrokerAdapter):
    """Simulated broker with in-memory accounts, orders, and positions."""

    @property
    def broker_name(self) -> str:
        return "paper"

    def __init__(
        self,
        *,
        retry_policy: RetryPolicy | None = None,
        auto_reconnect: bool = True,
        max_reconnect_attempts: int = 5,
    ) -> None:
        super().__init__(
            retry_policy=retry_policy,
            auto_reconnect=auto_reconnect,
            max_reconnect_attempts=max_reconnect_attempts,
        )
        self._accounts: dict[str, BrokerAccount] = {}
        self._orders: dict[str, BrokerOrder] = {}
        self._positions: dict[str, BrokerPosition] = {}

    @property
    def capabilities(self) -> BrokerCapabilities:
        return BrokerCapabilities(
            supports_websocket=True,
            supports_stream_market_data=True,
            supports_stream_orders=True,
            supports_stream_positions=True,
            max_orders_per_second=100.0,
            supported_asset_classes=("equity", "futures", "crypto"),
            notes="In-memory simulation",
        )

    async def _validate_connection_impl(self) -> None:
        if not self._accounts:
            msg = "Paper account not initialized"
            raise ValueError(msg)

    async def _flatten_position_impl(self, account_id: str, symbol: str) -> BrokerOrder:
        pos_id = f"{account_id}:{symbol}"
        position = self._positions.get(pos_id)
        if position is None:
            msg = f"No position for {symbol}"
            raise ValueError(msg)
        close_side = (
            BrokerOrderSide.SELL
            if position.side == BrokerPositionSide.LONG
            else BrokerOrderSide.BUY
        )
        return self._place_order_sync(
            PlaceOrderRequest(
                account_id=account_id,
                symbol=symbol,
                side=close_side,
                order_type=BrokerOrderType.MARKET,
                quantity=position.quantity,
            ),
        )

    async def _stream_orders_impl(
        self,
        account_id: str,
        handler: StreamHandler,
    ) -> StreamSubscription:
        return await self.websocket.subscribe(f"orders:{account_id}", handler)

    async def _connect_impl(self, credentials: BrokerCredentials) -> None:
        account_name = str(credentials.data.get("account_name", "Paper Account"))
        account_id = str(credentials.data.get("account_id", "paper-default"))
        starting_balance = Decimal(str(credentials.data.get("starting_balance", "100000")))
        self._accounts[account_id] = BrokerAccount(
            id=account_id,
            name=account_name,
            balance=starting_balance,
            equity=starting_balance,
            is_live=False,
        )
        await self._connect_websocket("wss://paper.tradeflow.local/stream")

    async def fetch_accounts(self) -> list[BrokerAccount]:
        async def _fetch() -> list[BrokerAccount]:
            return list(self._accounts.values())

        return await self._execute("fetch_accounts", _fetch)

    async def fetch_orders(self, account_id: str) -> list[BrokerOrder]:
        async def _fetch() -> list[BrokerOrder]:
            return [o for o in self._orders.values() if o.account_id == account_id]

        return await self._execute("fetch_orders", _fetch)

    async def fetch_positions(self, account_id: str) -> list[BrokerPosition]:
        async def _fetch() -> list[BrokerPosition]:
            return [p for p in self._positions.values() if p.account_id == account_id]

        return await self._execute("fetch_positions", _fetch)

    async def place_order(self, request: PlaceOrderRequest) -> BrokerOrder:
        async def _place() -> BrokerOrder:
            return self._place_order_sync(request)

        return await self._execute("place_order", _place)

    async def modify_order(self, order_id: str, request: ModifyOrderRequest) -> BrokerOrder:
        async def _modify() -> BrokerOrder:
            return self._modify_order_sync(order_id, request)

        return await self._execute("modify_order", _modify)

    async def cancel_order(self, order_id: str) -> BrokerOrder:
        async def _cancel() -> BrokerOrder:
            return self._cancel_order_sync(order_id)

        return await self._execute("cancel_order", _cancel)

    def _place_order_sync(self, request: PlaceOrderRequest) -> BrokerOrder:
        order_id = str(uuid.uuid4())
        fill_price = request.price or Decimal("100")
        order = BrokerOrder(
            id=order_id,
            account_id=request.account_id,
            symbol=request.symbol,
            side=request.side,
            order_type=request.order_type,
            quantity=request.quantity,
            price=request.price,
            status=BrokerOrderStatus.FILLED
            if request.order_type == BrokerOrderType.MARKET
            else BrokerOrderStatus.OPEN,
            filled_quantity=request.quantity
            if request.order_type == BrokerOrderType.MARKET
            else Decimal("0"),
            created_at=datetime.now(tz=UTC),
        )
        self._orders[order_id] = order
        if order.status == BrokerOrderStatus.FILLED:
            self._apply_fill(request, fill_price)
        return order

    def _modify_order_sync(self, order_id: str, request: ModifyOrderRequest) -> BrokerOrder:
        existing = self._orders.get(order_id)
        if existing is None:
            msg = f"Order {order_id} not found"
            raise ValueError(msg)
        updated = BrokerOrder(
            id=existing.id,
            account_id=existing.account_id,
            symbol=existing.symbol,
            side=existing.side,
            order_type=existing.order_type,
            quantity=request.quantity or existing.quantity,
            price=request.price if request.price is not None else existing.price,
            status=existing.status,
            filled_quantity=existing.filled_quantity,
            created_at=existing.created_at,
        )
        self._orders[order_id] = updated
        return updated

    def _cancel_order_sync(self, order_id: str) -> BrokerOrder:
        existing = self._orders.get(order_id)
        if existing is None:
            msg = f"Order {order_id} not found"
            raise ValueError(msg)
        canceled = BrokerOrder(
            id=existing.id,
            account_id=existing.account_id,
            symbol=existing.symbol,
            side=existing.side,
            order_type=existing.order_type,
            quantity=existing.quantity,
            price=existing.price,
            status=BrokerOrderStatus.CANCELED,
            filled_quantity=existing.filled_quantity,
            created_at=existing.created_at,
        )
        self._orders[order_id] = canceled
        return canceled

    def _apply_fill(self, request: PlaceOrderRequest, fill_price: Decimal) -> None:
        pos_id = f"{request.account_id}:{request.symbol}"
        side = (
            BrokerPositionSide.LONG
            if request.side == BrokerOrderSide.BUY
            else BrokerPositionSide.SHORT
        )
        existing = self._positions.get(pos_id)
        if existing is None:
            self._positions[pos_id] = BrokerPosition(
                id=pos_id,
                account_id=request.account_id,
                symbol=request.symbol,
                side=side,
                quantity=request.quantity,
                entry_price=fill_price,
                mark_price=fill_price,
            )
            return
        new_qty = existing.quantity + request.quantity
        self._positions[pos_id] = BrokerPosition(
            id=pos_id,
            account_id=request.account_id,
            symbol=request.symbol,
            side=existing.side,
            quantity=new_qty,
            entry_price=existing.entry_price,
            mark_price=fill_price,
        )
