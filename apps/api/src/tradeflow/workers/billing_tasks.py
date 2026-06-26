"""Celery tasks for billing — usage snapshots."""

from __future__ import annotations

import asyncio
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from tradeflow.core.config import get_settings
from tradeflow.core.logging import configure_logging, get_logger
from tradeflow.db.models.user import User
from tradeflow.features.billing.entitlements import EntitlementService
from tradeflow.workers.celery_app import celery_app

logger = get_logger(__name__)


def _run_async(coro: Any) -> Any:
    return asyncio.run(coro)


@celery_app.task(name="tradeflow.workers.billing_tasks.snapshot_usage")  # type: ignore[untyped-decorator]
def snapshot_usage() -> dict[str, int]:
    """Record usage snapshots for all active users."""

    async def _snapshot() -> dict[str, int]:
        settings = get_settings()
        configure_logging(settings)
        engine = create_async_engine(str(settings.database_url), pool_pre_ping=True)
        session_factory = async_sessionmaker(engine, expire_on_commit=False)
        entitlements = EntitlementService()
        count = 0

        try:
            async with session_factory() as db:
                users = await db.scalars(
                    select(User).where(User.is_active.is_(True), User.deleted_at.is_(None)),
                )
                for user in users.all():
                    await entitlements.snapshot_usage(db, user.id)
                    count += 1
                await db.commit()
        finally:
            await engine.dispose()

        logger.info("usage_snapshots_recorded", count=count)
        return {"snapshots": count}

    return _run_async(_snapshot())
