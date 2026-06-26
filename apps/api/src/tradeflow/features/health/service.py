from __future__ import annotations

import time
from datetime import UTC, datetime
from typing import Any

from redis.asyncio import Redis
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine

from tradeflow import __version__
from tradeflow.core.config import Settings
from tradeflow.features.health.schemas import (
    ComponentHealth,
    HealthStatus,
    HealthSummaryResponse,
    LivenessResponse,
    ReadinessResponse,
)


class HealthService:
    """Health check service with dependency probes."""

    def __init__(
        self,
        settings: Settings,
        db_engine: AsyncEngine,
        redis_client: Redis[Any],
    ) -> None:
        self._settings = settings
        self._db_engine = db_engine
        self._redis = redis_client

    def get_liveness(self) -> LivenessResponse:
        return LivenessResponse(
            service=self._settings.app_name,
            version=__version__,
            timestamp=datetime.now(tz=UTC),
        )

    async def get_readiness(self) -> ReadinessResponse:
        db_check = await self._check_database()
        redis_check = await self._check_redis()
        celery_broker_check = await self._check_celery_broker()

        checks = {
            "database": db_check,
            "redis": redis_check,
            "celery_broker": celery_broker_check,
        }

        statuses = [check.status for check in checks.values()]
        if all(status == HealthStatus.HEALTHY for status in statuses):
            overall = HealthStatus.HEALTHY
        elif any(status == HealthStatus.UNHEALTHY for status in statuses):
            overall = HealthStatus.UNHEALTHY
        else:
            overall = HealthStatus.DEGRADED

        return ReadinessResponse(
            status=overall,
            service=self._settings.app_name,
            version=__version__,
            timestamp=datetime.now(tz=UTC),
            checks=checks,
        )

    async def get_summary(self) -> HealthSummaryResponse:
        readiness = await self.get_readiness()
        return HealthSummaryResponse(
            status=readiness.status,
            service=readiness.service,
            version=readiness.version,
            environment=self._settings.app_env,
            timestamp=readiness.timestamp,
        )

    async def _check_database(self) -> ComponentHealth:
        start = time.perf_counter()
        try:
            async with self._db_engine.connect() as connection:
                await connection.execute(text("SELECT 1"))
            latency_ms = round((time.perf_counter() - start) * 1000, 2)
            return ComponentHealth(status=HealthStatus.HEALTHY, latency_ms=latency_ms)
        except Exception as exc:
            latency_ms = round((time.perf_counter() - start) * 1000, 2)
            return ComponentHealth(
                status=HealthStatus.UNHEALTHY,
                latency_ms=latency_ms,
                message=str(exc),
            )

    async def _check_redis(self) -> ComponentHealth:
        start = time.perf_counter()
        try:
            pong = await self._redis.ping()
            if not pong:
                msg = "Redis ping returned falsy response"
                raise RuntimeError(msg)
            latency_ms = round((time.perf_counter() - start) * 1000, 2)
            return ComponentHealth(status=HealthStatus.HEALTHY, latency_ms=latency_ms)
        except Exception as exc:
            latency_ms = round((time.perf_counter() - start) * 1000, 2)
            return ComponentHealth(
                status=HealthStatus.UNHEALTHY,
                latency_ms=latency_ms,
                message=str(exc),
            )

    async def _check_celery_broker(self) -> ComponentHealth:
        """Verify Celery message broker connectivity."""
        start = time.perf_counter()
        broker: Redis[Any] | None = None
        try:
            broker = Redis.from_url(
                str(self._settings.celery_broker_url),
                decode_responses=True,
            )
            pong = await broker.ping()
            if not pong:
                msg = "Celery broker ping returned falsy response"
                raise RuntimeError(msg)
            latency_ms = round((time.perf_counter() - start) * 1000, 2)
            return ComponentHealth(status=HealthStatus.HEALTHY, latency_ms=latency_ms)
        except Exception as exc:
            latency_ms = round((time.perf_counter() - start) * 1000, 2)
            return ComponentHealth(
                status=HealthStatus.UNHEALTHY,
                latency_ms=latency_ms,
                message=str(exc),
            )
        finally:
            if broker is not None:
                await broker.aclose()
