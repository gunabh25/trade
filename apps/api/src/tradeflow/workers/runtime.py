"""Shared DI container for Celery workers — mirrors the FastAPI service graph."""

from __future__ import annotations

from functools import lru_cache

from tradeflow.core.container import Container
from tradeflow.core.logging import configure_logging


@lru_cache(maxsize=1)
def get_worker_container() -> Container:
    """Process-scoped container singleton for background workers."""
    container = Container()
    configure_logging(container.config())
    return container
