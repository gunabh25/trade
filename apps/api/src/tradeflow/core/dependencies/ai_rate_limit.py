"""Per-user rate limits for AI generation endpoints."""

from __future__ import annotations

from dependency_injector.wiring import Provide, inject
from fastapi import Depends, Request

from tradeflow.core.config import Settings
from tradeflow.core.container import Container
from tradeflow.core.dependencies.auth import CurrentUser
from tradeflow.core.errors import RateLimitError
from tradeflow.core.security.rate_limit import RateLimiter

_MUTATING_METHODS = frozenset({"POST", "PUT", "PATCH", "DELETE"})


@inject
async def enforce_ai_rate_limit(
    request: Request,
    user: CurrentUser,
    settings: Settings = Depends(Provide[Container.config]),
    rate_limiter: RateLimiter = Depends(Provide[Container.rate_limiter]),
) -> None:
    if request.method not in _MUTATING_METHODS:
        return

    allowed, retry_after = await rate_limiter.check(
        f"ai:user:{user.id}",
        limit=settings.ai_rate_limit_per_minute,
        window_seconds=60,
    )
    if not allowed:
        raise RateLimitError(retry_after=retry_after)
