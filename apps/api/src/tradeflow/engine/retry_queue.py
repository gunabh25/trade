"""Redis-backed retry queue for failed copy executions."""

from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import UUID

from redis.asyncio import Redis

from tradeflow.core.logging import get_logger

logger = get_logger(__name__)

RETRY_QUEUE_KEY = "copy:retry:queue"
DEAD_LETTER_KEY = "copy:retry:dead_letter"
DEFAULT_MAX_ATTEMPTS = 5


class RetryQueue:
    """Priority retry queue using Redis sorted sets (score = next_retry_at epoch)."""

    def __init__(self, redis: Redis, max_attempts: int = DEFAULT_MAX_ATTEMPTS) -> None:  # type: ignore[type-arg]
        self._redis = redis
        self._max_attempts = max_attempts

    async def enqueue(
        self,
        *,
        execution_log_id: UUID,
        payload: dict[str, Any],
        attempt: int = 1,
        delay_seconds: float = 1.0,
    ) -> str:
        if attempt > self._max_attempts:
            await self._move_to_dead_letter(execution_log_id, payload)
            return "dead_letter"

        next_retry = datetime.now(tz=UTC) + timedelta(seconds=delay_seconds * (2 ** (attempt - 1)))
        item = json.dumps(
            {
                "execution_log_id": str(execution_log_id),
                "payload": payload,
                "attempt": attempt,
                "enqueued_at": datetime.now(tz=UTC).isoformat(),
            },
        )
        await self._redis.zadd(RETRY_QUEUE_KEY, {item: next_retry.timestamp()})
        logger.info(
            "copy_retry_enqueued",
            execution_log_id=str(execution_log_id),
            attempt=attempt,
            next_retry=next_retry.isoformat(),
        )
        return "queued"

    async def dequeue_ready(self, limit: int = 50) -> list[dict[str, Any]]:
        now = datetime.now(tz=UTC).timestamp()
        items = await self._redis.zrangebyscore(RETRY_QUEUE_KEY, "-inf", now, start=0, num=limit)
        if not items:
            return []

        pipe = self._redis.pipeline()
        for item in items:
            pipe.zrem(RETRY_QUEUE_KEY, item)
        await pipe.execute()

        return [json.loads(item) for item in items]

    async def queue_depth(self) -> int:
        return int(await self._redis.zcard(RETRY_QUEUE_KEY))

    async def dead_letter_count(self) -> int:
        return int(await self._redis.llen(DEAD_LETTER_KEY))

    async def _move_to_dead_letter(self, execution_log_id: UUID, payload: dict[str, Any]) -> None:
        item = json.dumps(
            {
                "execution_log_id": str(execution_log_id),
                "payload": payload,
                "dead_lettered_at": datetime.now(tz=UTC).isoformat(),
            },
        )
        await self._redis.lpush(DEAD_LETTER_KEY, item)
        logger.warning("copy_retry_dead_letter", execution_log_id=str(execution_log_id))
