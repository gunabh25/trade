"""Tests for leader stream event normalization."""

from __future__ import annotations

from uuid import uuid4

from tradeflow.db.enums import OrderSide
from tradeflow.engine.leader_events import order_stream_to_leader_event
from tradeflow.engine.types import LeaderEventType


def test_paper_order_stream_maps_to_submitted_event() -> None:
    group_id = uuid4()
    leader_id = uuid4()
    user_id = uuid4()

    event = order_stream_to_leader_event(
        copy_group_id=group_id,
        leader_account_id=leader_id,
        user_id=user_id,
        message={
            "type": "order",
            "broker": "paper",
            "order_id": "ord-123",
            "symbol": "ES",
            "side": "buy",
            "order_type": "market",
            "quantity": 2,
            "status": "filled",
            "stream_event": "order_submitted",
        },
    )

    assert event is not None
    assert event.event_type == LeaderEventType.ORDER_SUBMITTED
    assert event.leader_order_id == "ord-123"
    assert event.symbol == "ES"
    assert event.side == OrderSide.BUY
    assert event.quantity == 2


def test_cancelled_order_maps_to_cancel_event() -> None:
    event = order_stream_to_leader_event(
        copy_group_id=uuid4(),
        leader_account_id=uuid4(),
        user_id=uuid4(),
        message={
            "type": "order",
            "order_id": "ord-9",
            "symbol": "NQ",
            "side": "sell",
            "order_type": "limit",
            "quantity": 1,
            "status": "canceled",
        },
    )

    assert event is not None
    assert event.event_type == LeaderEventType.ORDER_CANCELLED
