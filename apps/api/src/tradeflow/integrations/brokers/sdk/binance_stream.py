"""Binance Spot WebSocket SDK — combined streams and user data."""

from __future__ import annotations

import json
from collections.abc import Awaitable, Callable
from typing import Any
from urllib.parse import urlencode

from tradeflow.core.logging import get_logger
from tradeflow.integrations.brokers.sdk.normalizers import (
    normalize_market_event,
    normalize_order_event,
)

logger = get_logger(__name__)

StreamCallback = Callable[[dict[str, Any]], Awaitable[None]]


class BinanceStreamClient:
    """Manage Binance Spot stream subscriptions with listen-key user data."""

    def __init__(
        self,
        *,
        api_key: str,
        signed_post: Callable[[str, dict[str, Any] | None], Awaitable[Any]],
        testnet: bool = False,
    ) -> None:
        self._api_key = api_key
        self._signed_post = signed_post
        self._testnet = testnet
        self._listen_key: str | None = None
        self._ws_url = (
            "wss://testnet.binance.vision/ws" if testnet else "wss://stream.binance.com:9443/ws"
        )
        self._combined_base = (
            "wss://testnet.binance.vision/stream"
            if testnet
            else "wss://stream.binance.com:9443/stream"
        )

    async def create_listen_key(self) -> str:
        data = await self._signed_post("/api/v3/userDataStream", {})
        key = str(data.get("listenKey", ""))
        if not key:
            msg = "Binance userDataStream did not return listenKey"
            raise ValueError(msg)
        self._listen_key = key
        return key

    async def keepalive_listen_key(self) -> None:
        if not self._listen_key:
            return
        await self._signed_post(
            "/api/v3/userDataStream",
            {"listenKey": self._listen_key},
        )

    def user_stream_url(self) -> str:
        if not self._listen_key:
            msg = "Listen key not created"
            raise ValueError(msg)
        return f"{self._ws_url}/{self._listen_key}"

    def market_stream_url(self, symbols: list[str]) -> str:
        streams = [f"{symbol.lower()}@trade" for symbol in symbols]
        query = urlencode({"streams": "/".join(streams)}, safe="/")
        return f"{self._combined_base}?{query}"

    async def dispatch_message(
        self,
        raw: str | bytes,
        *,
        on_order: StreamCallback | None = None,
        on_market: StreamCallback | None = None,
    ) -> None:
        try:
            payload = json.loads(raw) if isinstance(raw, (str, bytes)) else raw
        except json.JSONDecodeError:
            logger.warning("binance_stream_invalid_json")
            return
        if not isinstance(payload, dict):
            return

        data = payload.get("data", payload)
        if isinstance(data, dict) and data.get("e") == "executionReport" and on_order:
            await on_order(normalize_order_event("binance", data))
            return
        if on_market:
            event = normalize_market_event("binance", payload if "stream" in payload else data)
            if event.get("symbol") or event.get("price"):
                await on_market(event)
