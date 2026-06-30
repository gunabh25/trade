"""Tests for CSRF and AI rate limit middleware/dependencies."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest
from fastapi import Request

from tradeflow.core.config import Settings
from tradeflow.core.dependencies.ai_rate_limit import enforce_ai_rate_limit
from tradeflow.core.errors import ForbiddenError, RateLimitError
from tradeflow.core.security.cookies import validate_csrf


def _make_request(
    *,
    method: str = "POST",
    path: str = "/api/v1/journal/entries",
    cookies: dict[str, str] | None = None,
    headers: dict[str, str] | None = None,
) -> Request:
    scope = {
        "type": "http",
        "method": method,
        "path": path,
        "headers": [(k.lower().encode(), v.encode()) for k, v in (headers or {}).items()],
        "query_string": b"",
        "client": ("127.0.0.1", 12345),
        "server": ("testserver", 80),
    }
    request = Request(scope)
    if cookies:
        request._cookies = cookies
    return request


def test_validate_csrf_rejects_mismatch() -> None:
    settings = Settings(
        API_SECRET_KEY="x" * 32,
        AUTH_CSRF_COOKIE_NAME="tf_csrf",
    )
    request = _make_request(
        cookies={"tf_csrf": "cookie-token"},
        headers={"X-CSRF-Token": "header-token"},
    )
    with pytest.raises(ForbiddenError):
        validate_csrf(request, settings)


def test_validate_csrf_allows_matching_tokens() -> None:
    settings = Settings(
        API_SECRET_KEY="x" * 32,
        AUTH_CSRF_COOKIE_NAME="tf_csrf",
    )
    request = _make_request(
        cookies={"tf_csrf": "same-token"},
        headers={"X-CSRF-Token": "same-token"},
    )
    validate_csrf(request, settings)


@pytest.mark.asyncio
async def test_enforce_ai_rate_limit_blocks_when_exceeded() -> None:
    user = MagicMock()
    user.id = uuid4()
    request = _make_request(method="POST", path="/api/v1/ai/chat")
    settings = Settings(API_SECRET_KEY="x" * 32, AI_RATE_LIMIT_PER_MINUTE=5)
    rate_limiter = AsyncMock()
    rate_limiter.check.return_value = (False, 42)

    with pytest.raises(RateLimitError) as exc_info:
        await enforce_ai_rate_limit(
            request,
            user,
            settings=settings,
            rate_limiter=rate_limiter,
        )

    assert exc_info.value.status_code == 429
    rate_limiter.check.assert_awaited_once_with(
        f"ai:user:{user.id}",
        limit=5,
        window_seconds=60,
    )


@pytest.mark.asyncio
async def test_enforce_ai_rate_limit_skips_get_requests() -> None:
    user = MagicMock()
    user.id = uuid4()
    request = _make_request(method="GET", path="/api/v1/ai/status")
    settings = Settings(API_SECRET_KEY="x" * 32)
    rate_limiter = AsyncMock()

    await enforce_ai_rate_limit(
        request,
        user,
        settings=settings,
        rate_limiter=rate_limiter,
    )

    rate_limiter.check.assert_not_called()
