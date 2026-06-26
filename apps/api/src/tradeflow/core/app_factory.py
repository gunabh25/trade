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

from tradeflow import __version__
from tradeflow.api.v1.router import v1_router
from tradeflow.core.config import Settings
from tradeflow.core.container import Container
from tradeflow.core.exception_handlers import register_exception_handlers
from tradeflow.core.logging import configure_logging, get_logger
from tradeflow.core.middleware import RequestContextMiddleware
from tradeflow.integrations.brokers.monitor import ConnectionMonitor

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    container: Container = app.state.container
    settings: Settings = container.config()
    configure_logging(settings)

    db_engine: AsyncEngine = container.db_engine()
    redis_client: Redis[Any] = container.redis_client()
    connection_monitor: ConnectionMonitor = container.connection_monitor()

    logger.info(
        "application_starting",
        app_name=settings.app_name,
        environment=settings.app_env,
        version=__version__,
    )

    await connection_monitor.start()

    try:
        yield
    finally:
        await connection_monitor.stop()
        await redis_client.close()
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
        docs_url="/api/docs",
        redoc_url="/api/redoc",
        openapi_url="/api/openapi.json",
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
            "tradeflow.core.dependencies.auth",
        ],
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=["*"],
        expose_headers=["X-Request-ID"],
    )
    app.add_middleware(RequestContextMiddleware)

    register_exception_handlers(app)
    app.include_router(v1_router, prefix="/api")

    avatar_dir = Path(settings.avatar_upload_dir)
    avatar_dir.mkdir(parents=True, exist_ok=True)
    app.mount("/uploads/avatars", StaticFiles(directory=str(avatar_dir)), name="avatars")

    @app.get("/", include_in_schema=False)
    async def root() -> dict[str, str]:
        return {
            "service": settings.app_name,
            "version": __version__,
            "docs": "/api/docs",
        }

    return app
