"""Celery tasks for risk engine — background monitoring and session resets."""

from __future__ import annotations

import asyncio
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from tradeflow.core.config import get_settings
from tradeflow.core.logging import configure_logging, get_logger
from tradeflow.core.security.encryption import EncryptionService
from tradeflow.integrations.brokers.manager import BrokerSessionManager
from tradeflow.integrations.brokers.monitor import ConnectionMonitor
from tradeflow.integrations.brokers.registry import BrokerAdapterRegistry
from tradeflow.risk.actions import RiskActionExecutor
from tradeflow.risk.alerts import RiskAlertService
from tradeflow.risk.evaluator import RiskEvaluator
from tradeflow.risk.monitor import RiskMonitor
from tradeflow.risk.state import RiskStateStore
from tradeflow.workers.celery_app import celery_app

logger = get_logger(__name__)


def _run_async(coro: Any) -> Any:
    return asyncio.run(coro)


def _build_monitor() -> tuple[RiskMonitor, async_sessionmaker[AsyncSession], Any]:
    settings = get_settings()
    configure_logging(settings)

    engine = create_async_engine(str(settings.database_url), pool_pre_ping=True)
    session_factory = async_sessionmaker(engine, expire_on_commit=False)

    import redis.asyncio as aioredis

    redis = aioredis.from_url(str(settings.redis_url), decode_responses=True)
    encryption = EncryptionService(settings=settings)
    registry = BrokerAdapterRegistry()
    monitor_conn = ConnectionMonitor()
    session_manager = BrokerSessionManager(registry, monitor_conn, encryption)
    state_store = RiskStateStore(redis)
    evaluator = RiskEvaluator(state_store)
    action_executor = RiskActionExecutor(session_manager, state_store)
    alert_service = RiskAlertService(state_store)
    monitor = RiskMonitor(
        evaluator,
        action_executor,
        alert_service,
        state_store,
        session_manager,
    )
    return monitor, session_factory, redis


@celery_app.task(name="tradeflow.workers.risk_tasks.monitor_all_accounts")  # type: ignore[untyped-decorator]
def monitor_all_accounts() -> dict[str, int]:
    """Background job — evaluate all enabled risk rules."""

    async def _monitor() -> dict[str, int]:
        monitor, session_factory, redis = _build_monitor()
        try:
            async with session_factory() as db:
                result = await monitor.monitor_all(db)
                await db.commit()
            return result
        finally:
            await redis.close()

    return _run_async(_monitor())


@celery_app.task(name="tradeflow.workers.risk_tasks.reset_daily_sessions")  # type: ignore[untyped-decorator]
def reset_daily_sessions() -> dict[str, int]:
    """Reset daily P&L counters at session boundaries."""

    async def _reset() -> dict[str, int]:
        monitor, session_factory, redis = _build_monitor()
        try:
            async with session_factory() as db:
                count = await monitor.reset_daily_sessions(db)
                await db.commit()
            return {"reset": count}
        finally:
            await redis.close()

    return _run_async(_reset())
