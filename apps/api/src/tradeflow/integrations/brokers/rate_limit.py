"""Token-bucket rate limiter for broker API calls."""

from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass, field


@dataclass
class TokenBucketRateLimiter:
    """Async token bucket — one instance per broker connection."""

    rate_per_second: float
    burst: float | None = None
    _tokens: float = field(init=False)
    _last_refill: float = field(init=False)
    _lock: asyncio.Lock = field(default_factory=asyncio.Lock, init=False)

    def __post_init__(self) -> None:
        capacity = self.burst if self.burst is not None else self.rate_per_second
        self._tokens = capacity
        self._last_refill = time.monotonic()

    async def acquire(self, tokens: float = 1.0) -> None:
        async with self._lock:
            now = time.monotonic()
            elapsed = now - self._last_refill
            capacity = self.burst if self.burst is not None else self.rate_per_second
            self._tokens = min(capacity, self._tokens + elapsed * self.rate_per_second)
            self._last_refill = now
            if self._tokens < tokens:
                wait = (tokens - self._tokens) / self.rate_per_second
                await asyncio.sleep(wait)
                self._tokens = 0.0
            else:
                self._tokens -= tokens
