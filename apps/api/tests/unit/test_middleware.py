"""Unit tests for security and rate-limit middleware."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest
from starlette.requests import Request
from starlette.responses import Response

from tradeflow.core.config import get_settings
from tradeflow.core.rate_limit_middleware import _EXEMPT_PREFIXES, GlobalRateLimitMiddleware
from tradeflow.core.security_middleware import SecurityHeadersMiddleware


def _make_request(path: str = "/api/v1/auth/me", host: str = "127.0.0.1") -> Request:
    scope = {
        "type": "http",
        "method": "GET",
        "path": path,
        "headers": [],
        "client": (host, 12345),
        "server": ("testserver", 80),
        "scheme": "http",
        "query_string": b"",
    }
    return Request(scope)


@pytest.mark.unit
@pytest.mark.asyncio
async def test_security_headers_applied_in_development() -> None:
    settings = get_settings()
    middleware = SecurityHeadersMiddleware(MagicMock(), settings)
    request = _make_request()

    async def call_next(_: Request) -> Response:
        return Response(content="ok")

    response = await middleware.dispatch(request, call_next)
    assert response.headers["X-Content-Type-Options"] == "nosniff"
    assert response.headers["X-Frame-Options"] == "DENY"
    assert "Strict-Transport-Security" not in response.headers


@pytest.mark.unit
def test_rate_limit_exempt_paths_include_health_and_metrics() -> None:
    assert "/api/v1/health/live".startswith(_EXEMPT_PREFIXES[0])
    assert "/metrics".startswith(_EXEMPT_PREFIXES[1])


@pytest.mark.unit
@pytest.mark.asyncio
async def test_rate_limit_middleware_allows_under_limit() -> None:
    settings = get_settings()
    limiter = MagicMock()
    limiter.check = AsyncMock(return_value=(True, 0))
    middleware = GlobalRateLimitMiddleware(MagicMock(), settings, limiter)

    async def call_next(_: Request) -> Response:
        return Response(content="ok", status_code=200)

    response = await middleware.dispatch(_make_request(), call_next)
    assert response.status_code == 200
    assert response.headers["X-RateLimit-Limit"] == str(settings.api_rate_limit_per_minute)


@pytest.mark.unit
@pytest.mark.asyncio
async def test_rate_limit_middleware_blocks_over_limit() -> None:
    settings = get_settings()
    limiter = MagicMock()
    limiter.check = AsyncMock(return_value=(False, 30))
    middleware = GlobalRateLimitMiddleware(MagicMock(), settings, limiter)

    async def call_next(_: Request) -> Response:
        return Response(content="ok")

    response = await middleware.dispatch(_make_request(), call_next)
    assert response.status_code == 429
    assert response.headers["Retry-After"] == "30"


@pytest.mark.unit
@pytest.mark.asyncio
async def test_rate_limit_skips_exempt_health_path() -> None:
    settings = get_settings()
    limiter = MagicMock()
    limiter.check = AsyncMock()
    middleware = GlobalRateLimitMiddleware(MagicMock(), settings, limiter)

    async def call_next(_: Request) -> Response:
        return Response(content="ok")

    response = await middleware.dispatch(_make_request("/api/v1/health/live"), call_next)
    assert response.status_code == 200
    limiter.check.assert_not_called()
