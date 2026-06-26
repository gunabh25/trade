from __future__ import annotations

from typing import Literal, cast

from fastapi import Request, Response

from tradeflow.core.config import Settings
from tradeflow.core.errors import ForbiddenError


def set_auth_cookies(
    response: Response,
    settings: Settings,
    *,
    access_token: str,
    refresh_token: str,
    csrf_token: str,
) -> None:
    secure = settings.auth_cookie_secure
    samesite = cast(Literal["lax", "strict", "none"], settings.auth_cookie_samesite)
    domain = settings.auth_cookie_domain

    response.set_cookie(
        key=settings.auth_access_cookie_name,
        value=access_token,
        httponly=True,
        secure=secure,
        samesite=samesite,
        max_age=settings.jwt_access_token_expire_minutes * 60,
        domain=domain,
        path="/",
    )
    response.set_cookie(
        key=settings.auth_refresh_cookie_name,
        value=refresh_token,
        httponly=True,
        secure=secure,
        samesite=samesite,
        max_age=settings.jwt_refresh_token_expire_days * 86400,
        domain=domain,
        path="/api/v1/auth",
    )
    response.set_cookie(
        key=settings.auth_csrf_cookie_name,
        value=csrf_token,
        httponly=False,
        secure=secure,
        samesite=samesite,
        max_age=settings.jwt_refresh_token_expire_days * 86400,
        domain=domain,
        path="/",
    )


def clear_auth_cookies(response: Response, settings: Settings) -> None:
    domain = settings.auth_cookie_domain
    for name in (
        settings.auth_access_cookie_name,
        settings.auth_refresh_cookie_name,
        settings.auth_csrf_cookie_name,
    ):
        response.delete_cookie(key=name, path="/", domain=domain)
    response.delete_cookie(
        key=settings.auth_refresh_cookie_name,
        path="/api/v1/auth",
        domain=domain,
    )


def get_access_token_from_request(request: Request, settings: Settings) -> str | None:
    cookie_token = request.cookies.get(settings.auth_access_cookie_name)
    if cookie_token:
        return cookie_token
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.lower().startswith("bearer "):
        return auth_header[7:].strip()
    return None


def get_refresh_token_from_request(request: Request, settings: Settings) -> str | None:
    return request.cookies.get(settings.auth_refresh_cookie_name)


def validate_csrf(request: Request, settings: Settings) -> None:
    if request.method in {"GET", "HEAD", "OPTIONS"}:
        return
    cookie_token = request.cookies.get(settings.auth_csrf_cookie_name)
    header_token = request.headers.get("X-CSRF-Token")
    if not cookie_token or not header_token or cookie_token != header_token:
        raise ForbiddenError("CSRF validation failed")
