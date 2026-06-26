"""Celery tasks for risk engine — background monitoring and session resets."""

from __future__ import annotations

import asyncio
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from tradeflow.core.logging import get_logger
from tradeflow.risk.monitor import RiskMonitor
from tradeflow.workers.celery_app import celery_app
from tradeflow.workers.runtime import get_worker_container

logger = get_logger(__name__)


def _run_async(coro: Any) -> Any:
    return asyncio.run(coro)


def _build_monitor() -> tuple[RiskMonitor, async_sessionmaker[AsyncSession]]:
    container = get_worker_container()
    return container.risk_monitor(), container.db_session_factory()


@celery_app.task(name="tradeflow.workers.risk_tasks.monitor_all_accounts")  # type: ignore[untyped-decorator]
def monitor_all_accounts() -> dict[str, int]:
    """Background job — evaluate all enabled risk rules."""

    async def _monitor() -> dict[str, int]:
        monitor, session_factory = _build_monitor()
        async with session_factory() as db:
            result = await monitor.monitor_all(db)
            await db.commit()
        return result

    return _run_async(_monitor())


@celery_app.task(name="tradeflow.workers.risk_tasks.reset_daily_sessions")  # type: ignore[untyped-decorator]
def reset_daily_sessions() -> dict[str, int]:
    """Reset daily P&L counters at session boundaries."""

    async def _reset() -> dict[str, int]:
        monitor, session_factory = _build_monitor()
        async with session_factory() as db:
            count = await monitor.reset_daily_sessions(db)
            await db.commit()
        return {"reset": count}

    return _run_async(_reset())
