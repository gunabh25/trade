"""Plan limits and usage tracking."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from tradeflow.db.enums import SubscriptionStatus, UsageMetric
from tradeflow.db.models.billing import Plan, Subscription, UsageRecord
from tradeflow.db.models.broker import BrokerConnection
from tradeflow.db.models.copy_trading import CopyGroup
from tradeflow.db.models.trading import TradingAccount
from tradeflow.features.billing.schemas import UsageItemResponse


@dataclass(frozen=True)
class PlanLimits:
    max_trading_accounts: int
    max_broker_connections: int
    max_copy_groups: int


class EntitlementService:
    """Resolves active plan limits and records metered usage."""

    async def get_active_subscription(
        self,
        db: AsyncSession,
        user_id: UUID,
    ) -> Subscription | None:
        return await db.scalar(
            select(Subscription)
            .options(selectinload(Subscription.plan))
            .where(
                Subscription.user_id == user_id,
                Subscription.deleted_at.is_(None),
                Subscription.status.in_(
                    [
                        SubscriptionStatus.ACTIVE,
                        SubscriptionStatus.TRIALING,
                        SubscriptionStatus.PAST_DUE,
                    ],
                ),
            )
            .order_by(Subscription.created_at.desc())
            .limit(1),
        )

    async def get_plan_limits(self, db: AsyncSession, user_id: UUID) -> PlanLimits:
        subscription = await self.get_active_subscription(db, user_id)
        if subscription is None:
            free_plan = await self.get_plan_by_code(db, "free")
            if free_plan is None:
                return PlanLimits(2, 1, 1)
            return PlanLimits(
                free_plan.max_trading_accounts,
                free_plan.max_broker_connections,
                free_plan.max_copy_groups,
            )
        plan = subscription.plan
        return PlanLimits(
            plan.max_trading_accounts,
            plan.max_broker_connections,
            plan.max_copy_groups,
        )

    async def get_plan_by_code(self, db: AsyncSession, code: str) -> Plan | None:
        return await db.scalar(
            select(Plan).where(Plan.code == code, Plan.deleted_at.is_(None)),
        )

    async def count_current_usage(self, db: AsyncSession, user_id: UUID) -> dict[UsageMetric, int]:
        accounts = await db.scalar(
            select(func.count())
            .select_from(TradingAccount)
            .where(
                TradingAccount.user_id == user_id,
                TradingAccount.deleted_at.is_(None),
            ),
        )
        connections = await db.scalar(
            select(func.count())
            .select_from(BrokerConnection)
            .where(
                BrokerConnection.user_id == user_id,
                BrokerConnection.deleted_at.is_(None),
            ),
        )
        copy_groups = await db.scalar(
            select(func.count())
            .select_from(CopyGroup)
            .where(
                CopyGroup.user_id == user_id,
                CopyGroup.deleted_at.is_(None),
            ),
        )
        return {
            UsageMetric.TRADING_ACCOUNTS: int(accounts or 0),
            UsageMetric.BROKER_CONNECTIONS: int(connections or 0),
            UsageMetric.COPY_GROUPS: int(copy_groups or 0),
            UsageMetric.API_REQUESTS: 0,
        }

    async def get_usage_summary(
        self,
        db: AsyncSession,
        user_id: UUID,
    ) -> list[UsageItemResponse]:
        limits = await self.get_plan_limits(db, user_id)
        usage = await self.count_current_usage(db, user_id)
        limit_map = {
            UsageMetric.TRADING_ACCOUNTS: limits.max_trading_accounts,
            UsageMetric.BROKER_CONNECTIONS: limits.max_broker_connections,
            UsageMetric.COPY_GROUPS: limits.max_copy_groups,
            UsageMetric.API_REQUESTS: 10_000,
        }
        items: list[UsageItemResponse] = []
        for metric, used in usage.items():
            limit = limit_map[metric]
            percent = round((used / limit) * 100, 1) if limit > 0 else 0.0
            items.append(
                UsageItemResponse(metric=metric, used=used, limit=limit, percent=min(percent, 100)),
            )
        return items

    async def assert_within_limit(
        self,
        db: AsyncSession,
        user_id: UUID,
        metric: UsageMetric,
    ) -> None:
        from tradeflow.core.errors import ForbiddenError

        limits = await self.get_plan_limits(db, user_id)
        usage = await self.count_current_usage(db, user_id)
        limit_map = {
            UsageMetric.TRADING_ACCOUNTS: limits.max_trading_accounts,
            UsageMetric.BROKER_CONNECTIONS: limits.max_broker_connections,
            UsageMetric.COPY_GROUPS: limits.max_copy_groups,
        }
        limit = limit_map.get(metric)
        if limit is None:
            return
        if usage.get(metric, 0) >= limit:
            raise ForbiddenError(f"Plan limit reached for {metric.value.replace('_', ' ')}")

    async def snapshot_usage(
        self,
        db: AsyncSession,
        user_id: UUID,
        *,
        period_start: datetime | None = None,
        period_end: datetime | None = None,
    ) -> None:
        now = datetime.now(tz=UTC)
        start = period_start or now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        end = period_end or now
        usage = await self.count_current_usage(db, user_id)
        for metric, quantity in usage.items():
            existing = await db.scalar(
                select(UsageRecord).where(
                    UsageRecord.user_id == user_id,
                    UsageRecord.metric == metric,
                    UsageRecord.period_start == start,
                ),
            )
            if existing is None:
                db.add(
                    UsageRecord(
                        user_id=user_id,
                        metric=metric,
                        quantity=quantity,
                        period_start=start,
                        period_end=end,
                    ),
                )
            else:
                existing.quantity = quantity
                existing.period_end = end
        await db.flush()
