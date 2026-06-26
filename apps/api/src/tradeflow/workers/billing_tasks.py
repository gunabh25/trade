"""Celery tasks for billing — usage snapshots and trial lifecycle."""

from __future__ import annotations

import asyncio
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from tradeflow.core.logging import get_logger
from tradeflow.db.models.user import User
from tradeflow.features.billing.entitlements import EntitlementService
from tradeflow.features.billing.service import BillingService
from tradeflow.workers.celery_app import celery_app
from tradeflow.workers.runtime import get_worker_container

logger = get_logger(__name__)


def _run_async(coro: Any) -> Any:
    return asyncio.run(coro)


def _worker_session() -> tuple[
    BillingService,
    EntitlementService,
    async_sessionmaker[AsyncSession],
]:
    container = get_worker_container()
    return (
        container.billing_service(),
        container.entitlement_service(),
        container.db_session_factory(),
    )


@celery_app.task(name="tradeflow.workers.billing_tasks.snapshot_usage")  # type: ignore[untyped-decorator]
def snapshot_usage() -> dict[str, int]:
    """Record usage snapshots for all active users."""

    async def _snapshot() -> dict[str, int]:
        _, entitlements, session_factory = _worker_session()
        count = 0
        async with session_factory() as db:
            users = await db.scalars(
                select(User).where(User.is_active.is_(True), User.deleted_at.is_(None)),
            )
            for user in users.all():
                await entitlements.snapshot_usage(db, user.id)
                count += 1
            await db.commit()

        logger.info("usage_snapshots_recorded", count=count)
        return {"snapshots": count}

    return _run_async(_snapshot())


@celery_app.task(name="tradeflow.workers.billing_tasks.process_expired_trials")  # type: ignore[untyped-decorator]
def process_expired_trials() -> dict[str, int]:
    """Downgrade subscriptions whose trial period ended without payment."""

    async def _process() -> dict[str, int]:
        billing, _, session_factory = _worker_session()
        async with session_factory() as db:
            count = await billing.process_expired_trials(db)
            await db.commit()
        logger.info("expired_trials_processed", count=count)
        return {"processed": count}

    return _run_async(_process())
