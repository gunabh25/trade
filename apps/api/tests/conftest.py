"""Pytest configuration and shared fixtures."""

from __future__ import annotations

import os
from collections.abc import AsyncIterator

import pytest
import redis.asyncio as aioredis
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine

from tradeflow.core.app_factory import create_app

os.environ.setdefault(
    "API_SECRET_KEY",
    "test-secret-key-minimum-thirty-two-characters-long",
)
os.environ.setdefault(
    "DATABASE_URL",
    "postgresql+asyncpg://tradeflow:tradeflow_dev_password@localhost:5432/tradeflow",
)
os.environ.setdefault(
    "DATABASE_URL_SYNC",
    "postgresql+psycopg://tradeflow:tradeflow_dev_password@localhost:5432/tradeflow",
)
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")
os.environ.setdefault("CELERY_BROKER_URL", "redis://localhost:6379/1")
os.environ.setdefault("CELERY_RESULT_BACKEND", "redis://localhost:6379/2")
os.environ.setdefault("CELERY_TASK_ALWAYS_EAGER", "true")
os.environ.setdefault("FRONTEND_URL", "http://localhost:3000")
os.environ.setdefault("OAUTH_REDIRECT_BASE_URL", "http://testserver")
os.environ.setdefault("PROMETHEUS_ENABLED", "true")
os.environ.setdefault("APP_ENV", "development")
# Full integration suites register many users from the same test client IP.
os.environ["AUTH_RATE_LIMIT_PER_MINUTE"] = "10000"
os.environ["API_RATE_LIMIT_PER_MINUTE"] = "10000"


def pytest_configure(config: pytest.Config) -> None:
    config.addinivalue_line("markers", "unit: Pure unit tests (no I/O)")
    config.addinivalue_line("markers", "integration: Tests requiring PostgreSQL")
    config.addinivalue_line("markers", "api: HTTP API tests")
    config.addinivalue_line("markers", "slow: Slow tests")


@pytest.fixture(autouse=True)
def _mock_broker_websocket(monkeypatch: pytest.MonkeyPatch) -> None:
    """Prevent broker adapter tests from opening real network sockets."""

    async def _noop_connect_websocket(
        self: object,
        url: str,
        *,
        headers: dict[str, str] | None = None,
    ) -> None:
        return None

    from tradeflow.integrations.brokers.base import BaseBrokerAdapter

    monkeypatch.setattr(BaseBrokerAdapter, "_connect_websocket", _noop_connect_websocket)


@pytest.fixture(autouse=True)
async def _reset_rate_limit_counters() -> AsyncIterator[None]:
    """Clear Redis rate-limit state so repeated test runs do not flake."""
    try:
        client = aioredis.from_url(os.environ["REDIS_URL"], decode_responses=True)
        keys: list[str] = []
        async for key in client.scan_iter("ratelimit:*"):
            keys.append(key)
        async for key in client.scan_iter("auth:attempts:*"):
            keys.append(key)
        async for key in client.scan_iter("auth:lockout:*"):
            keys.append(key)
        if keys:
            await client.delete(*keys)
        await client.aclose()
    except OSError:
        pass
    yield


@pytest.fixture
def app():
    return create_app()


@pytest.fixture
async def client(app) -> AsyncIterator[AsyncClient]:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as ac:
        yield ac


@pytest.fixture
async def redis_client() -> AsyncIterator[aioredis.Redis]:
    client = aioredis.from_url(os.environ["REDIS_URL"], decode_responses=True)
    yield client
    await client.aclose()


@pytest.fixture
async def db_engine() -> AsyncIterator[AsyncEngine]:
    engine = create_async_engine(os.environ["DATABASE_URL"], pool_pre_ping=True)
    yield engine
    await engine.dispose()


@pytest.fixture
async def db_ready(db_engine: AsyncEngine) -> AsyncEngine:
    """Skip integration tests when PostgreSQL is unavailable or unmigrated."""
    try:
        async with db_engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
            result = await conn.execute(
                text(
                    "SELECT EXISTS (SELECT 1 FROM information_schema.tables "
                    "WHERE table_name = 'users')",
                ),
            )
            if not result.scalar():
                pytest.skip("Database schema not migrated — run alembic upgrade head")
    except Exception as exc:
        pytest.skip(f"Database unavailable: {exc}")
    return db_engine


@pytest.fixture
async def authenticated_client(client: AsyncClient, db_ready) -> AsyncClient:
    from tests.support.auth_helpers import register_and_login

    await register_and_login(client)
    return client
