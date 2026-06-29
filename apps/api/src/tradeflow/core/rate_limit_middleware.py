"""Global API rate limiting per client IP."""

from __future__ import annotations

from collections.abc import Awaitable, Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from tradeflow.core.config import Settings
from tradeflow.core.security.rate_limit import RateLimiter

_EXEMPT_PREFIXES = (
    "/api/v1/health",
    "/metrics",
    "/api/docs",
    "/api/redoc",
    "/api/openapi.json",
    "/uploads/",
)


class GlobalRateLimitMiddleware(BaseHTTPMiddleware):
    """Sliding-window rate limit for all API routes except health/metrics."""

    def __init__(
        self,
        app: object,
        settings: Settings,
        rate_limiter: RateLimiter,
    ) -> None:
        super().__init__(app)
        self._limit = settings.api_rate_limit_per_minute
        self._rate_limiter = rate_limiter

    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        path = request.url.path
        if any(path.startswith(prefix) for prefix in _EXEMPT_PREFIXES):
            return await call_next(request)

        client_ip = request.client.host if request.client else "unknown"
        allowed, retry_after = await self._rate_limiter.check(
            f"api:global:{client_ip}",
            limit=self._limit,
            window_seconds=60,
        )
        if not allowed:
            return JSONResponse(
                status_code=429,
                content={
                    "error": {
                        "code": "RATE_LIMIT_EXCEEDED",
                        "message": "Too many requests. Please slow down.",
                        "details": {"retryAfterSeconds": retry_after},
                    },
                },
                headers={"Retry-After": str(retry_after)},
            )

        response = await call_next(request)
        response.headers["X-RateLimit-Limit"] = str(self._limit)
        return response
