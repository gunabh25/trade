"""CSRF protection for cookie-authenticated API mutations."""

from __future__ import annotations

from collections.abc import Awaitable, Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from tradeflow.core.config import Settings
from tradeflow.core.security.cookies import validate_csrf

_EXEMPT_PREFIXES = (
    "/api/v1/health",
    "/api/v1/auth/oauth",
    "/api/v1/billing/webhooks",
    "/api/v1/broker/webhooks",
    "/metrics",
    "/uploads/",
)

_SAFE_METHODS = frozenset({"GET", "HEAD", "OPTIONS"})


class CsrfMiddleware(BaseHTTPMiddleware):
    """Validate CSRF token on mutating requests when using cookie auth."""

    def __init__(self, app: object, settings: Settings) -> None:
        super().__init__(app)
        self._settings = settings

    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        if request.method in _SAFE_METHODS:
            return await call_next(request)

        path = request.url.path
        if not path.startswith("/api/v1/"):
            return await call_next(request)

        if any(path.startswith(prefix) for prefix in _EXEMPT_PREFIXES):
            return await call_next(request)

        settings = self._settings
        access_cookie = request.cookies.get(settings.auth_access_cookie_name)
        if not access_cookie:
            auth_header = request.headers.get("Authorization", "")
            if auth_header.lower().startswith("bearer "):
                return await call_next(request)
            return await call_next(request)

        validate_csrf(request, settings)
        return await call_next(request)
