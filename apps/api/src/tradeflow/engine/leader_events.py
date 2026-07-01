"""Convert broker stream payloads into copy-engine leader events."""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation
from typing import Any
from uuid import UUID

from tradeflow.db.enums import OrderSide, OrderType
from tradeflow.engine.types import LeaderEvent, LeaderEventType


def leader_event_to_payload(event: LeaderEvent) -> dict[str, Any]:
    return {
        "id": event.id,
        "copy_group_id": str(event.copy_group_id),
        "leader_account_id": str(event.leader_account_id),
        "user_id": str(event.user_id),
        "event_type": event.event_type.value,
        "leader_order_id": event.leader_order_id,
        "symbol": event.symbol,
        "side": event.side.value,
        "order_type": event.order_type.value,
        "quantity": event.quantity,
        "price": str(event.price) if event.price is not None else None,
        "stop_price": str(event.stop_price) if event.stop_price is not None else None,
        "filled_quantity": event.filled_quantity,
    }


def _parse_decimal(value: object | None) -> Decimal | None:
    if value is None or value == "":
        return None
    try:
        return Decimal(str(value))
    except (InvalidOperation, ValueError):
        return None


def _parse_int(value: object | None, default: int = 0) -> int:
    if value is None or value == "":
        return default
    try:
        return int(Decimal(str(value)))
    except (InvalidOperation, ValueError):
        return default


def _map_stream_event_type(message: dict[str, Any], status: str) -> LeaderEventType | None:
    explicit = message.get("stream_event") or message.get("event_type")
    if isinstance(explicit, str):
        mapping = {
            "order_submitted": LeaderEventType.ORDER_SUBMITTED,
            "submitted": LeaderEventType.ORDER_SUBMITTED,
            "order_modified": LeaderEventType.ORDER_MODIFIED,
            "modified": LeaderEventType.ORDER_MODIFIED,
            "order_cancelled": LeaderEventType.ORDER_CANCELLED,
            "cancelled": LeaderEventType.ORDER_CANCELLED,
            "canceled": LeaderEventType.ORDER_CANCELLED,
            "fill": LeaderEventType.FILL,
            "filled": LeaderEventType.FILL,
            "partial_fill": LeaderEventType.PARTIAL_FILL,
        }
        normalized = explicit.lower()
        if normalized in mapping:
            return mapping[normalized]

    if status in {"canceled", "cancelled"}:
        return LeaderEventType.ORDER_CANCELLED
    if status in {"filled", "closed"}:
        return LeaderEventType.FILL
    if status in {"partially_filled", "partial"}:
        return LeaderEventType.PARTIAL_FILL
    if status in {"open", "new", "pending", "working"}:
        return LeaderEventType.ORDER_SUBMITTED
    return LeaderEventType.ORDER_SUBMITTED


def order_stream_to_leader_event(
    *,
    copy_group_id: UUID,
    leader_account_id: UUID,
    user_id: UUID,
    message: dict[str, Any],
) -> LeaderEvent | None:
    if message.get("type") not in {None, "order"}:
        return None

    order_id = str(message.get("order_id") or message.get("id") or "")
    symbol = str(message.get("symbol") or "")
    if not order_id or not symbol:
        return None

    status = str(message.get("status", "open")).lower()
    event_type = _map_stream_event_type(message, status)
    if event_type is None:
        return None

    side_raw = str(message.get("side", "buy")).lower()
    side = OrderSide.SELL if side_raw in {"sell", "short"} else OrderSide.BUY

    order_type_raw = str(message.get("order_type", "market")).lower()
    try:
        order_type = OrderType(order_type_raw)
    except ValueError:
        order_type = OrderType.MARKET

    quantity = _parse_int(message.get("quantity"), default=1)
    filled_quantity = _parse_int(message.get("filled_quantity"), default=0)
    timestamp = datetime.now(tz=UTC)
    event_id = f"{copy_group_id}:{order_id}:{event_type.value}:{int(timestamp.timestamp())}"

    return LeaderEvent(
        id=event_id,
        copy_group_id=copy_group_id,
        leader_account_id=leader_account_id,
        user_id=user_id,
        event_type=event_type,
        leader_order_id=order_id,
        symbol=symbol,
        side=side,
        order_type=order_type,
        quantity=quantity,
        price=_parse_decimal(message.get("price")),
        stop_price=_parse_decimal(message.get("stop_price")),
        filled_quantity=filled_quantity,
        timestamp=timestamp,
        raw=message,
    )
