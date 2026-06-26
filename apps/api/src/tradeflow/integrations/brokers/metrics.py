"""Broker integration metrics collector."""

from __future__ import annotations

import time
from collections import defaultdict
from dataclasses import dataclass, field
from threading import Lock


@dataclass
class OperationMetrics:
    count: int = 0
    errors: int = 0
    total_latency_ms: float = 0.0

    @property
    def avg_latency_ms(self) -> float:
        return self.total_latency_ms / self.count if self.count else 0.0


@dataclass
class BrokerMetricsCollector:
    """Thread-safe in-process metrics for broker operations."""

    _operations: dict[str, OperationMetrics] = field(
        default_factory=lambda: defaultdict(OperationMetrics),
    )
    _lock: Lock = field(default_factory=Lock)

    def record(self, operation: str, *, latency_ms: float, error: bool = False) -> None:
        with self._lock:
            m = self._operations[operation]
            m.count += 1
            m.total_latency_ms += latency_ms
            if error:
                m.errors += 1

    def snapshot(self) -> dict[str, dict[str, float | int]]:
        with self._lock:
            return {
                op: {
                    "count": m.count,
                    "errors": m.errors,
                    "avg_latency_ms": round(m.avg_latency_ms, 2),
                }
                for op, m in self._operations.items()
            }


_global_metrics = BrokerMetricsCollector()


def get_broker_metrics() -> BrokerMetricsCollector:
    return _global_metrics


class MetricsTimer:
    """Context manager to record operation latency."""

    def __init__(self, broker: str, operation: str) -> None:
        self._key = f"{broker}.{operation}"
        self._start = 0.0
        self._error = False

    def __enter__(self) -> MetricsTimer:
        self._start = time.perf_counter()
        return self

    def __exit__(self, exc_type: object, exc: object, tb: object) -> None:
        latency = (time.perf_counter() - self._start) * 1000
        self._error = exc is not None
        parts = self._key.split(".", 1)
        broker = parts[0]
        operation = parts[1] if len(parts) > 1 else self._key
        get_broker_metrics().record(f"{broker}.{operation}", latency_ms=latency, error=self._error)
