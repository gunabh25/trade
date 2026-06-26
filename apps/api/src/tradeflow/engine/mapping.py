"""Trade/order mapping — Redis hot cache + PostgreSQL persistence."""

from __future__ import annotations

import json
from uuid import UUID

from redis.asyncio import Redis
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from tradeflow.core.logging import get_logger
from tradeflow.db.enums import OrderLegType
from tradeflow.db.models.copy_trading import OrderMapping

logger = get_logger(__name__)

DEDUPE_TTL_SECONDS = 86_400
MAPPING_TTL_SECONDS = 604_800  # 7 days


class TradeMappingStore:
    """Dual-layer order mapping: Redis for ultra-low latency, DB for durability."""

    def __init__(self, redis: Redis) -> None:  # type: ignore[type-arg]
        self._redis = redis

    async def is_duplicate(self, leader_event_id: str) -> bool:
        key = f"copy:dedupe:{leader_event_id}"
        was_set = await self._redis.set(key, "1", ex=DEDUPE_TTL_SECONDS, nx=True)
        return was_set is None

    async def store_mapping(
        self,
        db: AsyncSession,
        *,
        copy_group_id: UUID,
        leader_order_id: str,
        follower_account_id: UUID,
        follower_order_id: str,
        leg_type: OrderLegType = OrderLegType.ENTRY,
        leader_order_db_id: UUID | None = None,
        follower_order_db_id: UUID | None = None,
    ) -> OrderMapping:
        mapping = OrderMapping(
            copy_group_id=copy_group_id,
            leader_order_id=leader_order_id,
            follower_account_id=follower_account_id,
            follower_order_id=follower_order_id,
            leg_type=leg_type,
            leader_order_db_id=leader_order_db_id,
            follower_order_db_id=follower_order_db_id,
        )
        db.add(mapping)
        await db.flush()

        cache_key = self._cache_key(copy_group_id, leader_order_id, follower_account_id, leg_type)
        await self._redis.set(
            cache_key,
            follower_order_id,
            ex=MAPPING_TTL_SECONDS,
        )
        logger.debug(
            "order_mapping_stored",
            copy_group_id=str(copy_group_id),
            leader_order_id=leader_order_id,
            follower_order_id=follower_order_id,
        )
        return mapping

    async def lookup_follower_order(
        self,
        db: AsyncSession,
        *,
        copy_group_id: UUID,
        leader_order_id: str,
        follower_account_id: UUID,
        leg_type: OrderLegType = OrderLegType.ENTRY,
    ) -> str | None:
        cache_key = self._cache_key(copy_group_id, leader_order_id, follower_account_id, leg_type)
        cached = await self._redis.get(cache_key)
        if cached:
            return str(cached)

        result = await db.scalar(
            select(OrderMapping.follower_order_id).where(
                OrderMapping.copy_group_id == copy_group_id,
                OrderMapping.leader_order_id == leader_order_id,
                OrderMapping.follower_account_id == follower_account_id,
                OrderMapping.leg_type == leg_type,
            ),
        )
        if result:
            await self._redis.set(cache_key, result, ex=MAPPING_TTL_SECONDS)
        return result

    async def build_lookup(
        self,
        db: AsyncSession,
        copy_group_id: UUID,
        leader_order_id: str,
    ) -> dict[tuple[str, UUID], str]:
        """Build in-memory lookup for all followers for a leader order."""
        rows = await db.scalars(
            select(OrderMapping).where(
                OrderMapping.copy_group_id == copy_group_id,
                OrderMapping.leader_order_id == leader_order_id,
            ),
        )
        return {
            (row.leader_order_id, row.follower_account_id): row.follower_order_id
            for row in rows.all()
        }

    async def publish_event(self, user_id: UUID, event: dict[str, object]) -> None:
        channel = f"copy:events:{user_id}"
        await self._redis.publish(channel, json.dumps(event))

    @staticmethod
    def _cache_key(
        copy_group_id: UUID,
        leader_order_id: str,
        follower_account_id: UUID,
        leg_type: OrderLegType,
    ) -> str:
        return (
            f"copy:mapping:{copy_group_id}:{leader_order_id}:{follower_account_id}:{leg_type.value}"
        )
