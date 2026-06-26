"""Retry utilities for broker API calls."""

from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from typing import TypeVar

from tradeflow.core.logging import get_logger
from tradeflow.integrations.brokers.exceptions import BrokerTransientError

logger = get_logger(__name__)

T = TypeVar("T")


@dataclass(frozen=True)
class RetryPolicy:
    max_attempts: int = 3
    base_delay_seconds: float = 0.5
    max_delay_seconds: float = 8.0
    exponential_base: float = 2.0


async def with_retry(
    operation: Callable[[], Awaitable[T]],
    *,
    policy: RetryPolicy,
    operation_name: str,
) -> T:
    """Execute an async operation with exponential backoff retry."""
    last_error: Exception | None = None
    delay = policy.base_delay_seconds

    for attempt in range(1, policy.max_attempts + 1):
        try:
            return await operation()
        except BrokerTransientError as exc:
            last_error = exc
            if attempt >= policy.max_attempts:
                break
            logger.warning(
                "broker_retry",
                operation=operation_name,
                attempt=attempt,
                max_attempts=policy.max_attempts,
                delay_seconds=delay,
                error=str(exc),
            )
            await asyncio.sleep(delay)
            delay = min(delay * policy.exponential_base, policy.max_delay_seconds)

    assert last_error is not None
    raise last_error
