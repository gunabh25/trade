"""Redis-backed API request metering for plan usage limits."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

from redis.asyncio import Redis


class UsageMeter:
    """Tracks monthly API request counts per user in Redis."""

    def __init__(self, redis: Redis) -> None:  # type: ignore[type-arg]
        self._redis = redis

    def _month_key(self, user_id: UUID) -> str:
        month = datetime.now(tz=UTC).strftime("%Y-%m")
        return f"usage:api_requests:{user_id}:{month}"

    async def increment_api_requests(self, user_id: UUID, amount: int = 1) -> int:
        key = self._month_key(user_id)
        value = await self._redis.incrby(key, amount)
        if value == amount:
            await self._redis.expire(key, 60 * 60 * 24 * 45)
        return int(value)

    async def get_api_requests(self, user_id: UUID) -> int:
        raw = await self._redis.get(self._month_key(user_id))
        return int(raw or 0)
