"""Sentry error tracking with credential scrubbing."""

from __future__ import annotations

from typing import Any

from tradeflow.core.config import Settings
from tradeflow.core.logging import get_logger

logger = get_logger(__name__)

_SENSITIVE_KEYS = frozenset(
    {
        "password",
        "token",
        "secret",
        "authorization",
        "cookie",
        "api_key",
        "credentials",
        "refresh_token",
        "access_token",
        "csrf",
    },
)


def _scrub_sensitive_data(event: dict[str, Any], _hint: dict[str, Any]) -> dict[str, Any] | None:
    """Remove tokens and credentials before events leave the process."""
    request = event.get("request")
    if isinstance(request, dict):
        headers = request.get("headers")
        if isinstance(headers, dict):
            for key in list(headers.keys()):
                if key.lower() in {"authorization", "cookie", "x-csrf-token"}:
                    headers[key] = "[Filtered]"
        data = request.get("data")
        if isinstance(data, dict):
            for key in list(data.keys()):
                if any(part in key.lower() for part in _SENSITIVE_KEYS):
                    data[key] = "[Filtered]"
    return event


def init_sentry(settings: Settings) -> None:
    """Initialize Sentry when SENTRY_DSN is configured."""
    if not settings.sentry_dsn:
        return

    try:
        import sentry_sdk
        from sentry_sdk.integrations.fastapi import FastApiIntegration
        from sentry_sdk.integrations.redis import RedisIntegration
        from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration
        from sentry_sdk.integrations.starlette import StarletteIntegration
    except ImportError:
        logger.warning("sentry_sdk_not_installed")
        return

    environment = settings.sentry_environment or settings.app_env
    sentry_sdk.init(
        dsn=settings.sentry_dsn,
        environment=environment,
        release=settings.app_version,
        traces_sample_rate=settings.sentry_traces_sample_rate,
        profiles_sample_rate=settings.sentry_profiles_sample_rate,
        send_default_pii=False,
        before_send=_scrub_sensitive_data,
        integrations=[
            StarletteIntegration(transaction_style="endpoint"),
            FastApiIntegration(transaction_style="endpoint"),
            SqlalchemyIntegration(),
            RedisIntegration(),
        ],
    )
    logger.info("sentry_initialized", environment=environment)
