"""Celery tasks for async notification delivery and scheduled alerts."""

from __future__ import annotations

import asyncio
from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from tradeflow.core.logging import get_logger
from tradeflow.db.enums import SubscriptionStatus
from tradeflow.db.models.billing import Plan, Subscription
from tradeflow.db.models.trading import TradingAccount
from tradeflow.notifications.dispatcher import NotificationDispatcher
from tradeflow.workers.celery_app import celery_app
from tradeflow.workers.runtime import get_worker_container

logger = get_logger(__name__)


def _run_async(coro: Any) -> Any:
    return asyncio.run(coro)


def _worker_session() -> tuple[NotificationDispatcher, async_sessionmaker[AsyncSession]]:
    container = get_worker_container()
    return container.notification_dispatcher(), container.db_session_factory()


@celery_app.task(name="tradeflow.workers.notification_tasks.deliver_notification_channels")  # type: ignore[untyped-decorator]
def deliver_notification_channels(
    user_id: str,
    event: str,
    rendered: dict[str, Any],
    channels: list[str],
) -> dict[str, Any]:
    """Deliver notification to external channels asynchronously."""

    async def _deliver() -> dict[str, Any]:
        dispatcher, session_factory = _worker_session()
        async with session_factory() as db:
            results = await dispatcher.deliver_external(
                db,
                user_id=UUID(user_id),
                event_value=event,
                rendered_dict=rendered,
                channel_values=channels,
            )
            await db.commit()
        return {"delivered": len(results), "results": results}

    return _run_async(_deliver())


@celery_app.task(name="tradeflow.workers.notification_tasks.check_subscription_expiry")  # type: ignore[untyped-decorator]
def check_subscription_expiry() -> dict[str, int]:
    """Notify users whose subscriptions expire within 7 days."""

    async def _check() -> dict[str, int]:
        dispatcher, session_factory = _worker_session()
        sent = 0
        cutoff = datetime.now(tz=UTC) + timedelta(days=7)
        async with session_factory() as db:
            rows = await db.execute(
                select(Subscription, Plan)
                .join(Plan, Subscription.plan_id == Plan.id)
                .where(
                    Subscription.status == SubscriptionStatus.ACTIVE,
                    Subscription.current_period_end.is_not(None),
                    Subscription.current_period_end <= cutoff,
                    Subscription.deleted_at.is_(None),
                ),
            )
            for subscription, plan in rows.all():
                days = max(
                    0,
                    (subscription.current_period_end - datetime.now(tz=UTC)).days,
                )
                await dispatcher.notify_subscription_expiry(
                    db,
                    user_id=subscription.user_id,
                    plan_name=plan.name,
                    days_remaining=days,
                    subscription_id=subscription.id,
                )
                sent += 1
            await db.commit()

        logger.info("subscription_expiry_notifications_sent", count=sent)
        return {"sent": sent}

    return _run_async(_check())


@celery_app.task(name="tradeflow.workers.notification_tasks.check_pnl_milestones")  # type: ignore[untyped-decorator]
def check_pnl_milestones() -> dict[str, int]:
    """Notify users when account equity crosses configured PnL milestones."""

    milestones = [10_000, 25_000, 50_000, 100_000, 250_000, 500_000, 1_000_000]

    async def _check() -> dict[str, int]:
        dispatcher, session_factory = _worker_session()
        sent = 0
        async with session_factory() as db:
            accounts = await db.scalars(
                select(TradingAccount).where(TradingAccount.deleted_at.is_(None)),
            )
            for account in accounts.all():
                equity = float(account.balance or 0)
                meta = account.metadata_ or {}
                reached = set(meta.get("pnl_milestones_reached", []))
                for milestone in milestones:
                    label = f"${milestone:,} equity"
                    if equity >= milestone and label not in reached:
                        await dispatcher.notify_pnl_milestone(
                            db,
                            user_id=account.user_id,
                            milestone_label=label,
                            pnl=equity,
                            account_id=account.id,
                        )
                        reached.add(label)
                        sent += 1
                if reached != set(meta.get("pnl_milestones_reached", [])):
                    account.metadata_ = {**meta, "pnl_milestones_reached": sorted(reached)}
            await db.commit()

        logger.info("pnl_milestone_notifications_sent", count=sent)
        return {"sent": sent}

    return _run_async(_check())
