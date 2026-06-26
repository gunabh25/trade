"""Celery background workers."""

from tradeflow.workers import copy_tasks  # noqa: F401 — register tasks
from tradeflow.workers.celery_app import celery_app

__all__ = ["celery_app"]
