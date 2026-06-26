"""Copy sizing strategies — fixed qty, risk multiplier, percentage, reverse."""

from __future__ import annotations

from decimal import ROUND_HALF_UP, Decimal

from tradeflow.db.enums import CopyMode, OrderSide
from tradeflow.engine.types import FollowerContext, LeaderEvent


def calculate_follower_quantity(
    event: LeaderEvent,
    follower: FollowerContext,
) -> tuple[int, OrderSide]:
    """Return (quantity, side) for the follower order based on copy mode."""
    leader_qty = event.quantity
    side = event.side

    if follower.copy_mode == CopyMode.FIXED_QUANTITY:
        qty = int(follower.sizing_value.to_integral_value(rounding=ROUND_HALF_UP))
    elif follower.copy_mode == CopyMode.RISK_MULTIPLIER:
        qty = int(
            (Decimal(leader_qty) * follower.sizing_value).to_integral_value(
                rounding=ROUND_HALF_UP,
            ),
        )
    elif follower.copy_mode == CopyMode.PERCENTAGE_ALLOCATION:
        pct = follower.sizing_value / Decimal("100")
        qty = int((Decimal(leader_qty) * pct).to_integral_value(rounding=ROUND_HALF_UP))
    elif follower.copy_mode == CopyMode.REVERSE_COPY:
        qty = leader_qty
        side = OrderSide.SELL if event.side == OrderSide.BUY else OrderSide.BUY
    else:
        qty = leader_qty

    return max(0, qty), side


def calculate_partial_fill_quantity(
    event: LeaderEvent,
    follower: FollowerContext,
    leader_filled_qty: int,
) -> tuple[int, OrderSide]:
    """Scale partial fill proportionally to copy mode."""
    if leader_filled_qty <= 0 or event.quantity <= 0:
        return 0, event.side

    fill_ratio = Decimal(leader_filled_qty) / Decimal(event.quantity)
    full_qty, side = calculate_follower_quantity(event, follower)
    partial_qty = int(
        (Decimal(full_qty) * fill_ratio).to_integral_value(rounding=ROUND_HALF_UP),
    )
    return max(0, partial_qty), side
