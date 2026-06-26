"""WebSocket support for broker adapters."""

from __future__ import annotations

import asyncio
import contextlib
from collections.abc import Awaitable, Callable
from typing import Any

from tradeflow.core.logging import get_logger

logger = get_logger(__name__)

MessageHandler = Callable[[dict[str, Any]], Awaitable[None]]


class BrokerWebSocketManager:
    """Manages broker WebSocket lifecycle with automatic reconnect hooks."""

    def __init__(self, broker_name: str) -> None:
        self._broker_name = broker_name
        self._connected = False
        self._handlers: list[MessageHandler] = []
        self._listen_task: asyncio.Task[None] | None = None

    @property
    def is_connected(self) -> bool:
        return self._connected

    def on_message(self, handler: MessageHandler) -> None:
        self._handlers.append(handler)

    async def connect(self, url: str) -> None:
        """Establish WebSocket connection. Subclasses override for real WS."""
        logger.info("broker_websocket_connect", broker=self._broker_name, url=url)
        self._connected = True

    async def disconnect(self) -> None:
        if self._listen_task and not self._listen_task.done():
            self._listen_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self._listen_task
        self._connected = False
        logger.info("broker_websocket_disconnect", broker=self._broker_name)

    async def publish(self, message: dict[str, Any]) -> None:
        """Dispatch a message to registered handlers (used by adapters/simulation)."""
        for handler in self._handlers:
            await handler(message)

    async def simulate_reconnect(self) -> None:
        """Hook for adapters to trigger reconnect flow in tests."""
        logger.warning("broker_websocket_reconnect", broker=self._broker_name)
        self._connected = False
        await asyncio.sleep(0)
        self._connected = True
