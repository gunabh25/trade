import uuid
from collections.abc import AsyncGenerator

from dependency_injector import containers, providers
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from tradeflow.core.config import Settings, get_settings
from tradeflow.db.session import create_session_factory
from tradeflow.features.health.service import HealthService


class Container(containers.DeclarativeContainer):
    """Application dependency injection container."""

    wiring_config = containers.WiringConfiguration(
        modules=[
            "tradeflow.api.v1.router",
            "tradeflow.features.health.router",
        ],
    )

    config: providers.Singleton[Settings] = providers.Singleton(get_settings)

    db_engine: providers.Singleton[AsyncEngine] = providers.Singleton(
        create_async_engine,
        providers.Callable(str, config.provided.database_url),
        pool_size=config.provided.database_pool_size,
        max_overflow=config.provided.database_max_overflow,
        pool_timeout=config.provided.database_pool_timeout,
        pool_pre_ping=True,
        echo=config.provided.is_development,
    )

    db_session_factory: providers.Singleton[async_sessionmaker[AsyncSession]] = providers.Singleton(
        create_session_factory, db_engine
    )

    redis_client: providers.Singleton[Redis] = providers.Singleton(
        Redis.from_url,
        providers.Callable(str, config.provided.redis_url),
        decode_responses=True,
    )

    health_service: providers.Factory[HealthService] = providers.Factory(
        HealthService,
        settings=config,
        db_engine=db_engine,
        redis_client=redis_client,
    )


async def get_db_session(
    session_factory: async_sessionmaker[AsyncSession],
) -> AsyncGenerator[AsyncSession, None]:
    async with session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


def generate_request_id() -> str:
    return str(uuid.uuid4())
