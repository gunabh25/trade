"""Platform observability — Redis, Celery, queues, security telemetry."""

from __future__ import annotations

from typing import Any

from redis.asyncio import Redis
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from tradeflow.core.config import Settings
from tradeflow.db.enums import AuditAction, UsageMetric
from tradeflow.db.models.audit import AuditLog
from tradeflow.db.models.billing import UsageRecord
from tradeflow.db.models.notification_platform import NotificationDelivery
from tradeflow.features.health.service import HealthService


class AdminObservabilityService:
    """Aggregates operational metrics for the admin portal."""

    def __init__(
        self,
        settings: Settings,
        redis: Redis,  # type: ignore[type-arg]
        health_service: HealthService,
    ) -> None:
        self._settings = settings
        self._redis = redis
        self._health = health_service

    async def get_platform_metrics(self, db: AsyncSession) -> dict[str, Any]:
        readiness = await self._health.get_readiness()
        redis_info = await self._redis_info()
        celery = await self._celery_status()
        queues = await self._queue_status()
        security = await self._security_summary(db)
        api_usage = await self._api_usage_summary(db)
        rate_limits = await self._rate_limit_summary()
        notifications = await self._notification_delivery_summary(db)

        return {
            "health": {
                "status": readiness.status.value,
                "database": readiness.checks["database"].model_dump(),
                "redis": readiness.checks["redis"].model_dump(),
                "celery_broker": readiness.checks["celery_broker"].model_dump(),
            },
            "redis": redis_info,
            "celery": celery,
            "queues": queues,
            "security": security,
            "api_usage": api_usage,
            "rate_limits": rate_limits,
            "notifications": notifications,
            "websockets": {"status": "broker_adapters", "note": "Per-connection broker WebSockets"},
        }

    async def list_security_events(
        self,
        db: AsyncSession,
        *,
        page: int = 1,
        page_size: int = 50,
    ) -> tuple[list[dict[str, Any]], int]:
        query = select(AuditLog).where(
            AuditLog.action.in_(
                [
                    AuditAction.LOGIN,
                    AuditAction.LOGOUT,
                    AuditAction.ADMIN,
                    AuditAction.CREATE,
                    AuditAction.DELETE,
                ],
            ),
        )
        total = int(await db.scalar(select(func.count()).select_from(query.subquery())) or 0)
        rows = await db.scalars(
            query.order_by(AuditLog.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size),
        )
        items = [
            {
                "id": str(row.id),
                "action": row.action.value,
                "user_id": str(row.user_id) if row.user_id else None,
                "resource_type": row.resource_type,
                "ip_address": row.ip_address,
                "created_at": row.created_at.isoformat(),
                "metadata": row.metadata_,
            }
            for row in rows.all()
        ]
        return items, total

    async def list_failed_logins(self) -> list[dict[str, Any]]:
        lockouts: list[dict[str, Any]] = []
        async for key in self._redis.scan_iter(match="auth:lockout:*", count=200):
            email = key.removeprefix("auth:lockout:")
            ttl = int(await self._redis.ttl(key) or 0)
            attempts_raw = await self._redis.get(f"auth:attempts:{email}")
            lockouts.append(
                {
                    "email": email,
                    "locked": ttl > 0,
                    "retry_after_seconds": ttl if ttl > 0 else None,
                    "recent_attempts": int(attempts_raw or 0),
                },
            )
        return sorted(lockouts, key=lambda item: item["email"])[:100]

    async def _redis_info(self) -> dict[str, Any]:
        try:
            info = await self._redis.info(section="memory")
            db_size = await self._redis.dbsize()
            return {
                "status": "healthy",
                "used_memory_human": info.get("used_memory_human"),
                "connected_clients": info.get("connected_clients"),
                "keys": db_size,
            }
        except Exception as exc:
            return {"status": "unhealthy", "error": str(exc)}

    async def _celery_status(self) -> dict[str, Any]:
        broker_check = (await self._health.get_readiness()).checks["celery_broker"]
        result: dict[str, Any] = {
            "broker": broker_check.model_dump(),
            "workers": [],
            "active_tasks": 0,
        }
        try:
            from tradeflow.workers.celery_app import celery_app

            inspect = celery_app.control.inspect(timeout=2.0)
            if inspect is None:
                return result
            stats = inspect.stats() or {}
            active = inspect.active() or {}
            result["workers"] = [
                {"name": name, "pool": data.get("pool", {}).get("max-concurrency")}
                for name, data in stats.items()
            ]
            result["active_tasks"] = sum(len(tasks) for tasks in active.values())
            result["status"] = "healthy" if stats else "degraded"
        except Exception as exc:
            result["status"] = "unknown"
            result["error"] = str(exc)
        return result

    async def _queue_status(self) -> dict[str, Any]:
        copy_retry = 0
        async for _ in self._redis.scan_iter(match="copy:retry:*", count=500):
            copy_retry += 1
        notification_keys = 0
        async for _ in self._redis.scan_iter(match="usage:api_requests:*", count=500):
            notification_keys += 1
        return {
            "copy_retry_items": copy_retry,
            "usage_tracking_keys": notification_keys,
        }

    async def _security_summary(self, db: AsyncSession) -> dict[str, Any]:
        login_events = int(
            await db.scalar(
                select(func.count())
                .select_from(AuditLog)
                .where(AuditLog.action == AuditAction.LOGIN),
            )
            or 0,
        )
        admin_events = int(
            await db.scalar(
                select(func.count())
                .select_from(AuditLog)
                .where(AuditLog.action == AuditAction.ADMIN),
            )
            or 0,
        )
        lockouts = 0
        async for _ in self._redis.scan_iter(match="auth:lockout:*", count=500):
            lockouts += 1
        return {
            "total_logins": login_events,
            "admin_actions": admin_events,
            "active_lockouts": lockouts,
        }

    async def _api_usage_summary(self, db: AsyncSession) -> dict[str, Any]:
        rows = await db.execute(
            select(UsageRecord.metric, func.sum(UsageRecord.quantity)).group_by(UsageRecord.metric),
        )
        totals = {metric.value: int(qty or 0) for metric, qty in rows.all()}
        if UsageMetric.API_REQUESTS.value not in totals:
            api_keys = 0
            async for _ in self._redis.scan_iter(match="usage:api_requests:*", count=1000):
                api_keys += 1
            totals[UsageMetric.API_REQUESTS.value] = api_keys
        return {"totals_by_metric": totals}

    async def _rate_limit_summary(self) -> dict[str, Any]:
        active_limits = 0
        async for _ in self._redis.scan_iter(match="ratelimit:*", count=500):
            active_limits += 1
        return {"active_rate_limit_keys": active_limits}

    async def _notification_delivery_summary(self, db: AsyncSession) -> dict[str, Any]:
        pending = int(
            await db.scalar(
                select(func.count())
                .select_from(NotificationDelivery)
                .where(NotificationDelivery.status == "pending"),
            )
            or 0,
        )
        failed = int(
            await db.scalar(
                select(func.count())
                .select_from(NotificationDelivery)
                .where(NotificationDelivery.status == "failed"),
            )
            or 0,
        )
        sent = int(
            await db.scalar(
                select(func.count())
                .select_from(NotificationDelivery)
                .where(NotificationDelivery.status == "sent"),
            )
            or 0,
        )
        return {"pending": pending, "failed": failed, "sent": sent}
