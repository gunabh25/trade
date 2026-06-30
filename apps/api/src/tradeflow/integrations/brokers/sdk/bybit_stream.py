"""Bybit V5 WebSocket SDK — public and private topics."""

from __future__ import annotations

import hashlib
import hmac
import json
import time
from collections.abc import Awaitable, Callable
from typing import Any

from tradeflow.core.logging import get_logger
from tradeflow.integrations.brokers.sdk.normalizers import (
    normalize_market_event,
    normalize_order_event,
    normalize_position_event,
)

logger = get_logger(__name__)

StreamCallback = Callable[[dict[str, Any]], Awaitable[None]]


class BybitStreamClient:
    """Bybit V5 WebSocket auth and subscription helpers."""

    def __init__(
        self,
        *,
        api_key: str,
        api_secret: str,
        testnet: bool = False,
    ) -> None:
        self._api_key = api_key
        self._api_secret = api_secret
        self._testnet = testnet

    @property
    def private_url(self) -> str:
        if self._testnet:
            return "wss://stream-testnet.bybit.com/v5/private"
        return "wss://stream.bybit.com/v5/private"

    @property
    def public_linear_url(self) -> str:
        if self._testnet:
            return "wss://stream-testnet.bybit.com/v5/public/linear"
        return "wss://stream.bybit.com/v5/public/linear"

    def auth_payload(self) -> dict[str, Any]:
        expires = int(time.time() * 1000) + 10_000
        signature = hmac.new(
            self._api_secret.encode(),
            f"GET/realtime{expires}".encode(),
            hashlib.sha256,
        ).hexdigest()
        return {"op": "auth", "args": [self._api_key, expires, signature]}

    @staticmethod
    def subscribe_payload(topics: list[str]) -> dict[str, Any]:
        return {"op": "subscribe", "args": topics}

    def order_topics(self) -> list[str]:
        return ["order"]

    def position_topics(self) -> list[str]:
        return ["position"]

    def ticker_topics(self, symbols: list[str]) -> list[str]:
        return [f"tickers.{symbol}" for symbol in symbols]

    async def dispatch_message(
        self,
        raw: str | bytes,
        *,
        on_order: StreamCallback | None = None,
        on_position: StreamCallback | None = None,
        on_market: StreamCallback | None = None,
    ) -> None:
        try:
            payload = json.loads(raw) if isinstance(raw, (str, bytes)) else raw
        except json.JSONDecodeError:
            logger.warning("bybit_stream_invalid_json")
            return
        if not isinstance(payload, dict):
            return

        topic = str(payload.get("topic", ""))
        if topic.startswith("order") and on_order:
            await on_order(normalize_order_event("bybit", payload))
        elif topic.startswith("position") and on_position:
            await on_position(normalize_position_event("bybit", payload))
        elif ("tickers" in topic or "publicTrade" in topic) and on_market:
            await on_market(normalize_market_event("bybit", payload))
