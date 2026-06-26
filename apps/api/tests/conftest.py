import os

import pytest
import redis.asyncio as aioredis

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


@pytest.fixture
async def redis_client():
    client = aioredis.from_url(os.environ["REDIS_URL"], decode_responses=True)
    yield client
    await client.aclose()
