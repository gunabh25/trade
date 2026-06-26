from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncEngine

from tradeflow import __version__
from tradeflow.api.v1.router import v1_router
from tradeflow.core.config import Settings
from tradeflow.core.container import Container
from tradeflow.core.exception_handlers import register_exception_handlers
from tradeflow.core.logging import configure_logging, get_logger
from tradeflow.core.middleware import RequestContextMiddleware

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    container: Container = app.state.container
    settings: Settings = container.config()
    configure_logging(settings)

    db_engine: AsyncEngine = container.db_engine()
    redis_client: Redis = container.redis_client()

    logger.info(
        "application_starting",
        app_name=settings.app_name,
        environment=settings.app_env,
        version=__version__,
    )

    try:
        yield
    finally:
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
        docs_url="/api/docs",
        redoc_url="/api/redoc",
        openapi_url="/api/openapi.json",
        lifespan=lifespan,
    )

    app.state.container = di_container
    di_container.wire(
        modules=[
            "tradeflow.features.health.router",
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

    @app.get("/", include_in_schema=False)
    async def root() -> dict[str, str]:
        return {
            "service": settings.app_name,
            "version": __version__,
            "docs": "/api/docs",
        }

    return app
