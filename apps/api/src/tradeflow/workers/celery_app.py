from celery import Celery

from tradeflow.core.config import get_settings

settings = get_settings()

celery_app = Celery(
    "tradeflow",
    broker=str(settings.celery_broker_url),
    backend=str(settings.celery_result_backend),
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=300,
    task_soft_time_limit=240,
    worker_prefetch_multiplier=1,
    task_always_eager=settings.celery_task_always_eager,
    task_routes={
        "tradeflow.workers.tasks.*": {"queue": "default"},
        "tradeflow.workers.copy_tasks.*": {"queue": "copy"},
        "tradeflow.workers.risk_tasks.*": {"queue": "risk"},
        "tradeflow.workers.notification_tasks.*": {"queue": "notifications"},
        "tradeflow.workers.billing_tasks.*": {"queue": "default"},
    },
    beat_schedule={
        "drain-copy-retry-queue": {
            "task": "tradeflow.workers.copy_tasks.drain_retry_queue",
            "schedule": 5.0,
        },
        "recover-broker-connections": {
            "task": "tradeflow.workers.copy_tasks.recover_connections",
            "schedule": 60.0,
        },
        "monitor-risk-all-accounts": {
            "task": "tradeflow.workers.risk_tasks.monitor_all_accounts",
            "schedule": 30.0,
        },
        "reset-daily-risk-sessions": {
            "task": "tradeflow.workers.risk_tasks.reset_daily_sessions",
            "schedule": 3600.0,
        },
        "check-subscription-expiry": {
            "task": "tradeflow.workers.notification_tasks.check_subscription_expiry",
            "schedule": 86400.0,
        },
        "check-pnl-milestones": {
            "task": "tradeflow.workers.notification_tasks.check_pnl_milestones",
            "schedule": 3600.0,
        },
        "snapshot-billing-usage": {
            "task": "tradeflow.workers.billing_tasks.snapshot_usage",
            "schedule": 86400.0,
        },
    },
)

celery_app.autodiscover_tasks(["tradeflow.workers"])
