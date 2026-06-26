from __future__ import annotations

import secrets
from typing import Any

from redis.asyncio import Redis


class RateLimiter:
    """Redis sliding-window rate limiter."""

    def __init__(self, redis: Redis[Any]) -> None:
        self._redis = redis

    async def check(
        self,
        key: str,
        *,
        limit: int,
        window_seconds: int,
    ) -> tuple[bool, int]:
        """Return (allowed, retry_after_seconds)."""
        redis_key = f"ratelimit:{key}"
        count = await self._redis.incr(redis_key)
        if count == 1:
            await self._redis.expire(redis_key, window_seconds)
        if count > limit:
            ttl = await self._redis.ttl(redis_key)
            return False, max(ttl, 1)
        return True, 0


class LoginProtection:
    """Brute-force protection for credential login."""

    def __init__(self, redis: Redis[Any], *, max_attempts: int, lockout_seconds: int) -> None:
        self._redis = redis
        self._max_attempts = max_attempts
        self._lockout_seconds = lockout_seconds

    async def is_locked(self, email: str) -> tuple[bool, int]:
        lock_key = f"auth:lockout:{email.lower()}"
        ttl = await self._redis.ttl(lock_key)
        if ttl > 0:
            return True, ttl
        return False, 0

    async def record_failure(self, email: str) -> None:
        email_key = email.lower()
        attempts_key = f"auth:attempts:{email_key}"
        count = await self._redis.incr(attempts_key)
        if count == 1:
            await self._redis.expire(attempts_key, self._lockout_seconds)
        if count >= self._max_attempts:
            await self._redis.setex(
                f"auth:lockout:{email_key}",
                self._lockout_seconds,
                "1",
            )
            await self._redis.delete(attempts_key)

    async def reset(self, email: str) -> None:
        email_key = email.lower()
        await self._redis.delete(f"auth:attempts:{email_key}", f"auth:lockout:{email_key}")


def generate_csrf_token() -> str:
    return secrets.token_urlsafe(32)
