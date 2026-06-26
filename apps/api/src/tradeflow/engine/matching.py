"""Order matching — plan copy decisions from leader events."""

from __future__ import annotations

from uuid import UUID

from tradeflow.db.enums import (
    CopyEventAction,
    CopyFollowerStatus,
    CopyGroupStatus,
)
from tradeflow.db.models.copy_trading import CopyGroup, CopyGroupFollower
from tradeflow.engine.sizing import calculate_follower_quantity, calculate_partial_fill_quantity
from tradeflow.engine.types import CopyDecision, FollowerContext, LeaderEvent, LeaderEventType


class OrderMatcher:
    """Plans copy decisions for each follower given a leader event."""

    def plan_copies(
        self,
        event: LeaderEvent,
        group: CopyGroup,
        followers: list[CopyGroupFollower],
        follower_contexts: dict[UUID, FollowerContext],
        order_mapping_lookup: dict[tuple[str, UUID], str] | None = None,
    ) -> list[CopyDecision]:
        if group.status != CopyGroupStatus.ACTIVE or not group.copying_enabled:
            return []

        action = self._event_to_action(event.event_type)
        if action is None:
            return []

        mapping = order_mapping_lookup or {}
        decisions: list[CopyDecision] = []

        for follower in followers:
            ctx = follower_contexts.get(follower.follower_account_id)
            if ctx is None:
                continue

            decision = self._plan_single(event, follower, ctx, action, mapping)
            decisions.append(decision)

        return decisions

    def _plan_single(
        self,
        event: LeaderEvent,
        follower: CopyGroupFollower,
        ctx: FollowerContext,
        action: CopyEventAction,
        mapping: dict[tuple[str, UUID], str],
    ) -> CopyDecision:
        base = CopyDecision(
            follower_account_id=follower.follower_account_id,
            follower_config_id=follower.id,
            action=action,
            quantity=0,
            side=event.side,
            order_type=event.order_type,
            price=event.price,
            stop_price=event.stop_price,
            leg_type=event.leg_type,
        )

        if not follower.enabled:
            return self._skip(base, "disabled")
        if follower.status == CopyFollowerStatus.LOCKED:
            return self._skip(base, "locked")
        if follower.status == CopyFollowerStatus.PAUSED:
            return self._skip(base, "paused")

        if action in {CopyEventAction.MODIFY, CopyEventAction.CANCEL}:
            key = (event.leader_order_id, follower.follower_account_id)
            if key not in mapping:
                return self._skip(base, "no_mapping")

        if event.event_type == LeaderEventType.PARTIAL_FILL:
            qty, side = calculate_partial_fill_quantity(
                event,
                ctx,
                event.filled_quantity,
            )
        else:
            qty, side = calculate_follower_quantity(event, ctx)

        if qty <= 0:
            return self._skip(base, "size_zero")

        return CopyDecision(
            follower_account_id=follower.follower_account_id,
            follower_config_id=follower.id,
            action=action,
            quantity=qty,
            side=side,
            order_type=event.order_type,
            price=event.price,
            stop_price=event.stop_price,
            leg_type=event.leg_type,
        )

    @staticmethod
    def _event_to_action(event_type: LeaderEventType) -> CopyEventAction | None:
        mapping = {
            LeaderEventType.ORDER_SUBMITTED: CopyEventAction.PLACE,
            LeaderEventType.ORDER_MODIFIED: CopyEventAction.MODIFY,
            LeaderEventType.ORDER_CANCELLED: CopyEventAction.CANCEL,
            LeaderEventType.FILL: CopyEventAction.FILL,
            LeaderEventType.PARTIAL_FILL: CopyEventAction.PARTIAL_FILL,
        }
        return mapping.get(event_type)

    @staticmethod
    def _skip(decision: CopyDecision, reason: str) -> CopyDecision:
        return CopyDecision(
            follower_account_id=decision.follower_account_id,
            follower_config_id=decision.follower_config_id,
            action=decision.action,
            quantity=0,
            side=decision.side,
            order_type=decision.order_type,
            skip=True,
            skip_reason=reason,
        )
