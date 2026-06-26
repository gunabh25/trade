"""WebSocket support for broker adapters with reconnect hooks."""

from __future__ import annotations

import asyncio
import contextlib
import json
from typing import Any

from tradeflow.core.logging import get_logger
from tradeflow.integrations.brokers.types import StreamHandler, StreamSubscription

logger = get_logger(__name__)


class BrokerWebSocketManager:
    """Manages broker WebSocket lifecycle with handler dispatch and reconnect."""

    def __init__(self, broker_name: str) -> None:
        self._broker_name = broker_name
        self._connected = False
        self._handlers: list[StreamHandler] = []
        self._listen_task: asyncio.Task[None] | None = None
        self._ws: Any = None
        self._url: str | None = None
        self._headers: dict[str, str] = {}
        self._should_run = False

    @property
    def is_connected(self) -> bool:
        return self._connected

    def on_message(self, handler: StreamHandler) -> None:
        self._handlers.append(handler)

    async def connect(self, url: str, *, headers: dict[str, str] | None = None) -> None:
        """Establish WebSocket connection using websockets library when available."""
        self._url = url
        self._headers = headers or {}
        try:
            import websockets

            self._ws = await websockets.connect(url, additional_headers=self._headers)
            self._connected = True
            self._should_run = True
            self._listen_task = asyncio.create_task(self._listen_loop())
            logger.info("broker_websocket_connect", broker=self._broker_name, url=url)
        except ImportError:
            logger.warning(
                "broker_websocket_stub",
                broker=self._broker_name,
                reason="websockets package not installed",
            )
            self._connected = True
        except Exception as exc:
            logger.error(
                "broker_websocket_connect_failed",
                broker=self._broker_name,
                error=str(exc),
            )
            self._connected = False
            raise

    async def disconnect(self) -> None:
        self._should_run = False
        if self._listen_task and not self._listen_task.done():
            self._listen_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self._listen_task
        if self._ws is not None:
            with contextlib.suppress(Exception):
                await self._ws.close()
            self._ws = None
        self._connected = False
        logger.info("broker_websocket_disconnect", broker=self._broker_name)

    async def send(self, payload: dict[str, Any]) -> None:
        if self._ws is not None:
            await self._ws.send(json.dumps(payload))

    async def publish(self, message: dict[str, Any]) -> None:
        """Dispatch a message to registered handlers (simulation / inbound webhooks)."""
        for handler in self._handlers:
            await handler(message)

    async def subscribe(
        self,
        channel: str,
        handler: StreamHandler,
    ) -> StreamSubscription:
        self.on_message(handler)

        async def _unsubscribe() -> None:
            if handler in self._handlers:
                self._handlers.remove(handler)

        return StreamSubscription(channel=channel, unsubscribe=_unsubscribe)

    async def _listen_loop(self) -> None:
        while self._should_run and self._ws is not None:
            try:
                raw = await self._ws.recv()
                data = json.loads(raw) if isinstance(raw, str) else raw
                if isinstance(data, dict):
                    await self.publish(data)
            except asyncio.CancelledError:
                break
            except Exception as exc:
                logger.warning(
                    "broker_websocket_recv_error",
                    broker=self._broker_name,
                    error=str(exc),
                )
                await self._attempt_reconnect()
                await asyncio.sleep(1)

    async def _attempt_reconnect(self) -> None:
        if not self._url:
            return
        logger.warning("broker_websocket_reconnect", broker=self._broker_name)
        self._connected = False
        if self._ws is not None:
            with contextlib.suppress(Exception):
                await self._ws.close()
        await self.connect(self._url, headers=self._headers)

    async def simulate_reconnect(self) -> None:
        """Hook for adapters to trigger reconnect flow in tests."""
        await self._attempt_reconnect()
