from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncEngine
from starlette.middleware.gzip import GZipMiddleware
from starlette.middleware.trustedhost import TrustedHostMiddleware

from tradeflow import __version__
from tradeflow.api.v1.router import v1_router
from tradeflow.core.config import Settings
from tradeflow.core.container import Container
from tradeflow.core.exception_handlers import register_exception_handlers
from tradeflow.core.logging import configure_logging, get_logger
from tradeflow.core.middleware import RequestContextMiddleware
from tradeflow.core.observability.prometheus import (
    PrometheusMiddleware,
    metrics_router,
    setup_prometheus,
)
from tradeflow.core.observability.sentry import init_sentry
from tradeflow.core.rate_limit_middleware import GlobalRateLimitMiddleware
from tradeflow.core.security.rate_limit import RateLimiter
from tradeflow.core.security_middleware import SecurityHeadersMiddleware
from tradeflow.integrations.brokers.manager import BrokerSessionManager
from tradeflow.integrations.brokers.monitor import ConnectionMonitor

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    container: Container = app.state.container
    settings: Settings = container.config()
    configure_logging(settings)
    init_sentry(settings)

    if settings.prometheus_enabled:
        setup_prometheus()

    db_engine: AsyncEngine = container.db_engine()
    redis_client: Redis[Any] = container.redis_client()
    connection_monitor: ConnectionMonitor = container.connection_monitor()
    broker_sessions: BrokerSessionManager = container.broker_session_manager()

    logger.info(
        "application_starting",
        app_name=settings.app_name,
        environment=settings.app_env,
        version=__version__,
        workers=settings.api_workers,
    )

    await connection_monitor.start()

    try:
        yield
    finally:
        logger.info("application_shutting_down")
        await broker_sessions.disconnect_all()
        await connection_monitor.stop()
        await redis_client.aclose()
        await db_engine.dispose()
        logger.info("application_shutdown_complete")


def create_app(container: Container | None = None) -> FastAPI:
    """Application factory for production and test usage."""
    di_container = container or Container()
    settings = di_container.config()

    app = FastAPI(
        title=settings.app_name,
        description=(
            "TradeFlow AI — professional cloud-based multi-account trade copier, "
            "risk management, and trading analytics platform."
        ),
        version=__version__,
        docs_url=None if settings.is_production else "/api/docs",
        redoc_url=None if settings.is_production else "/api/redoc",
        openapi_url=None if settings.is_production else "/api/openapi.json",
        lifespan=lifespan,
    )

    app.state.container = di_container
    di_container.wire(
        modules=[
            "tradeflow.features.health.router",
            "tradeflow.features.auth.router",
            "tradeflow.features.broker.router",
            "tradeflow.features.copy_trading.router",
            "tradeflow.features.risk.router",
            "tradeflow.features.journal.router",
            "tradeflow.features.analytics.router",
            "tradeflow.features.notifications.router",
            "tradeflow.features.billing.router",
            "tradeflow.features.admin.router",
            "tradeflow.features.ai.router",
            "tradeflow.core.dependencies.auth",
        ],
    )

    if settings.trusted_hosts:
        app.add_middleware(TrustedHostMiddleware, allowed_hosts=settings.trusted_hosts)

    if settings.api_enable_gzip:
        app.add_middleware(GZipMiddleware, minimum_size=1000)

    app.add_middleware(SecurityHeadersMiddleware, settings=settings)

    if settings.prometheus_enabled:
        app.add_middleware(PrometheusMiddleware)

    rate_limiter = RateLimiter(di_container.redis_client())
    app.add_middleware(GlobalRateLimitMiddleware, settings=settings, rate_limiter=rate_limiter)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=["*"],
        expose_headers=["X-Request-ID", "X-RateLimit-Limit"],
    )
    app.add_middleware(RequestContextMiddleware)

    register_exception_handlers(app)
    app.include_router(v1_router, prefix="/api")

    if settings.prometheus_enabled:
        app.include_router(metrics_router)

    avatar_dir = Path(settings.avatar_upload_dir)
    avatar_dir.mkdir(parents=True, exist_ok=True)
    app.mount("/uploads/avatars", StaticFiles(directory=str(avatar_dir)), name="avatars")

    journal_dir = Path(settings.journal_upload_dir)
    journal_dir.mkdir(parents=True, exist_ok=True)
    app.mount("/uploads/journal", StaticFiles(directory=str(journal_dir)), name="journal")

    @app.get("/", include_in_schema=False)
    async def root() -> dict[str, str]:
        return {
            "service": settings.app_name,
            "version": __version__,
            "docs": "/api/docs" if not settings.is_production else "",
        }

    return app
