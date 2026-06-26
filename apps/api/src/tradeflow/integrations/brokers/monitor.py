"""Connection monitoring and automatic reconnect orchestration."""

from __future__ import annotations

import asyncio
import contextlib
from uuid import UUID

from tradeflow.core.logging import get_logger
from tradeflow.integrations.brokers.interface import BrokerAdapter
from tradeflow.integrations.brokers.types import BrokerHealthStatus, ConnectionHealth

logger = get_logger(__name__)


class ConnectionMonitor:
    """Tracks live adapter sessions and runs periodic health probes."""

    def __init__(self, *, health_check_interval_seconds: float = 30.0) -> None:
        self._adapters: dict[UUID, BrokerAdapter] = {}
        self._interval = health_check_interval_seconds
        self._task: asyncio.Task[None] | None = None
        self._running = False

    def register(self, connection_id: UUID, adapter: BrokerAdapter) -> None:
        self._adapters[connection_id] = adapter
        logger.info("broker_monitor_registered", connection_id=str(connection_id))

    def unregister(self, connection_id: UUID) -> None:
        self._adapters.pop(connection_id, None)
        logger.info("broker_monitor_unregistered", connection_id=str(connection_id))

    def get_health(self, connection_id: UUID) -> ConnectionHealth | None:
        adapter = self._adapters.get(connection_id)
        if adapter is None:
            return None
        return adapter.get_health()

    def get_all_health(self) -> dict[str, ConnectionHealth]:
        return {
            str(connection_id): adapter.get_health()
            for connection_id, adapter in self._adapters.items()
        }

    async def start(self) -> None:
        if self._running:
            return
        self._running = True
        self._task = asyncio.create_task(self._monitor_loop())
        logger.info("broker_monitor_started", interval_seconds=self._interval)

    async def stop(self) -> None:
        self._running = False
        if self._task and not self._task.done():
            self._task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self._task
        logger.info("broker_monitor_stopped")

    async def _monitor_loop(self) -> None:
        while self._running:
            await asyncio.sleep(self._interval)
            for connection_id, adapter in list(self._adapters.items()):
                health = adapter.get_health()
                if health.status == BrokerHealthStatus.ERROR:
                    logger.warning(
                        "broker_connection_unhealthy",
                        connection_id=str(connection_id),
                        error=health.last_error,
                    )
                elif not health.connected:
                    logger.warning(
                        "broker_connection_disconnected",
                        connection_id=str(connection_id),
                    )
