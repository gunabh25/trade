"""Copy engine unit tests."""

from __future__ import annotations

from decimal import Decimal
from uuid import uuid4

import pytest

from tradeflow.db.enums import CopyGroupStatus, CopyMode, OrderSide, OrderType
from tradeflow.db.models.copy_trading import CopyGroup, CopyGroupFollower
from tradeflow.engine.matching import OrderMatcher
from tradeflow.engine.sizing import calculate_follower_quantity, calculate_partial_fill_quantity
from tradeflow.engine.types import FollowerContext, LeaderEvent, LeaderEventType


def _event(qty: int = 2, side: OrderSide = OrderSide.BUY) -> LeaderEvent:
    return LeaderEvent(
        id="test-event-1",
        copy_group_id=uuid4(),
        leader_account_id=uuid4(),
        user_id=uuid4(),
        event_type=LeaderEventType.ORDER_SUBMITTED,
        leader_order_id="order-1",
        symbol="ES",
        side=side,
        order_type=OrderType.MARKET,
        quantity=qty,
    )


def _ctx(mode: CopyMode, value: Decimal) -> FollowerContext:
    return FollowerContext(
        follower_account_id=uuid4(),
        broker_connection_id=uuid4(),
        external_account_id="acct-1",
        copy_mode=mode,
        sizing_value=value,
        enabled=True,
        status="active",
    )


def test_fixed_quantity_sizing() -> None:
    qty, side = calculate_follower_quantity(_event(5), _ctx(CopyMode.FIXED_QUANTITY, Decimal("3")))
    assert qty == 3
    assert side == OrderSide.BUY


def test_risk_multiplier_sizing() -> None:
    qty, _ = calculate_follower_quantity(_event(4), _ctx(CopyMode.RISK_MULTIPLIER, Decimal("2")))
    assert qty == 8


def test_percentage_allocation_sizing() -> None:
    qty, _ = calculate_follower_quantity(
        _event(10),
        _ctx(CopyMode.PERCENTAGE_ALLOCATION, Decimal("50")),
    )
    assert qty == 5


def test_reverse_copy_flips_side() -> None:
    event = _event(2, OrderSide.BUY)
    ctx = _ctx(CopyMode.REVERSE_COPY, Decimal("1"))
    qty, side = calculate_follower_quantity(event, ctx)
    assert qty == 2
    assert side == OrderSide.SELL


def test_partial_fill_scaling() -> None:
    event = _event(10)
    qty, _ = calculate_partial_fill_quantity(event, _ctx(CopyMode.RISK_MULTIPLIER, Decimal("2")), 5)
    assert qty == 10  # half of leader fill → half of follower full size (20) = 10


def test_order_matcher_skips_disabled_follower() -> None:
    matcher = OrderMatcher()
    group = CopyGroup(
        id=uuid4(),
        user_id=uuid4(),
        leader_account_id=uuid4(),
        name="Test",
        mode="live",
        status=CopyGroupStatus.ACTIVE,
        copying_enabled=True,
    )
    follower_id = uuid4()
    follower = CopyGroupFollower(
        id=uuid4(),
        copy_group_id=group.id,
        follower_account_id=follower_id,
        enabled=False,
        copy_mode=CopyMode.FIXED_QUANTITY,
        sizing_value=Decimal("1"),
    )
    ctx = _ctx(CopyMode.FIXED_QUANTITY, Decimal("1"))
    ctx = FollowerContext(
        follower_account_id=follower_id,
        broker_connection_id=ctx.broker_connection_id,
        external_account_id=ctx.external_account_id,
        copy_mode=ctx.copy_mode,
        sizing_value=ctx.sizing_value,
        enabled=False,
        status="active",
    )
    decisions = matcher.plan_copies(_event(), group, [follower], {follower_id: ctx})
    assert len(decisions) == 1
    assert decisions[0].skip is True
    assert decisions[0].skip_reason == "disabled"


@pytest.mark.asyncio
async def test_retry_queue_enqueue_dequeue(redis_client) -> None:
    from tradeflow.engine.retry_queue import RetryQueue

    queue = RetryQueue(redis_client, max_attempts=3)
    log_id = uuid4()
    await queue.enqueue(
        execution_log_id=log_id,
        payload={"test": True},
        attempt=1,
        delay_seconds=0,
    )
    depth = await queue.queue_depth()
    assert depth >= 1
    items = await queue.dequeue_ready(limit=10)
    assert any(item["execution_log_id"] == str(log_id) for item in items)
