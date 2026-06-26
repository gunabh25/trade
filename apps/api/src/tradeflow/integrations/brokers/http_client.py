"""Shared HTTP client with error normalization for broker REST APIs."""

from __future__ import annotations

import json
from collections.abc import Awaitable, Callable, Mapping
from typing import Any

import httpx

from tradeflow.core.logging import get_logger
from tradeflow.integrations.brokers.errors import BrokerErrorCode
from tradeflow.integrations.brokers.exceptions import (
    BrokerAuthError,
    BrokerConnectionError,
    BrokerNotSupportedError,
    BrokerOrderError,
    BrokerRateLimitError,
    BrokerTransientError,
    NormalizedBrokerError,
)
from tradeflow.integrations.brokers.pool import BrokerHttpPool
from tradeflow.integrations.brokers.rate_limit import TokenBucketRateLimiter

logger = get_logger(__name__)

SignHeadersFn = Callable[[str, str, Mapping[str, Any] | None], dict[str, str]]


class BrokerHttpClient:
    """Production HTTP transport — pooling, rate limits, normalized errors."""

    def __init__(
        self,
        *,
        broker_name: str,
        pool: BrokerHttpPool,
        rate_limiter: TokenBucketRateLimiter,
        default_headers: dict[str, str] | None = None,
        sign_headers: SignHeadersFn | None = None,
    ) -> None:
        self._broker = broker_name
        self._pool = pool
        self._limiter = rate_limiter
        self._default_headers = default_headers or {}
        self._sign_headers = sign_headers

    async def close(self) -> None:
        await self._pool.close()

    async def request(
        self,
        method: str,
        path: str,
        *,
        params: dict[str, Any] | None = None,
        json_body: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
    ) -> Any:
        await self._limiter.acquire()

        client = await self._pool.get_client()
        merged_headers = {**self._default_headers, **(headers or {})}
        body_str = json.dumps(json_body, separators=(",", ":")) if json_body else ""
        if self._sign_headers is not None:
            merged_headers.update(self._sign_headers(method, path, params or json_body))

        try:
            response = await client.request(
                method,
                path,
                params=params,
                content=body_str if json_body else None,
                headers=merged_headers,
            )
        except httpx.TimeoutException as exc:
            raise BrokerTransientError(f"{self._broker} request timeout: {path}") from exc
        except httpx.HTTPError as exc:
            raise BrokerConnectionError(f"{self._broker} HTTP error: {exc}") from exc

        return self._normalize_response(response)

    async def get(self, path: str, *, params: dict[str, Any] | None = None) -> Any:
        return await self.request("GET", path, params=params)

    async def post(
        self,
        path: str,
        *,
        params: dict[str, Any] | None = None,
        json_body: dict[str, Any] | None = None,
    ) -> Any:
        return await self.request("POST", path, params=params, json_body=json_body)

    async def put(
        self,
        path: str,
        *,
        json_body: dict[str, Any] | None = None,
    ) -> Any:
        return await self.request("PUT", path, json_body=json_body)

    async def delete(self, path: str, *, params: dict[str, Any] | None = None) -> Any:
        return await self.request("DELETE", path, params=params)

    def _normalize_response(self, response: httpx.Response) -> Any:
        status = response.status_code
        text = response.text
        payload: Any
        try:
            payload = response.json() if text else {}
        except json.JSONDecodeError:
            payload = {"raw": text}

        if status == 429:
            raise BrokerRateLimitError(
                f"{self._broker} rate limited",
                code=BrokerErrorCode.RATE_LIMITED,
                broker=self._broker,
                http_status=status,
                raw=payload,
            )
        if status in {401, 403}:
            raise BrokerAuthError(
                f"{self._broker} authentication failed",
                code=BrokerErrorCode.AUTH_FAILED,
                broker=self._broker,
                http_status=status,
                raw=payload,
            )
        if status >= 500:
            raise BrokerTransientError(
                f"{self._broker} server error ({status})",
            )
        if status >= 400:
            code = self._map_error_code(status, payload)
            if code == BrokerErrorCode.NOT_SUPPORTED:
                raise BrokerNotSupportedError(str(payload))
            if code in {
                BrokerErrorCode.INVALID_ORDER,
                BrokerErrorCode.ORDER_NOT_FOUND,
                BrokerErrorCode.INSUFFICIENT_FUNDS,
            }:
                raise BrokerOrderError(
                    f"{self._broker} order error: {payload}",
                    code=code,
                    broker=self._broker,
                    http_status=status,
                    raw=payload,
                )
            raise NormalizedBrokerError(
                f"{self._broker} API error ({status}): {payload}",
                code=code,
                broker=self._broker,
                http_status=status,
                raw=payload,
            )

        return payload

    def _map_error_code(self, status: int, payload: Any) -> BrokerErrorCode:
        text = json.dumps(payload).lower() if payload else ""
        if "insufficient" in text or "margin" in text:
            return BrokerErrorCode.INSUFFICIENT_FUNDS
        if "not found" in text or status == 404:
            return BrokerErrorCode.ORDER_NOT_FOUND
        if "invalid" in text:
            return BrokerErrorCode.INVALID_ORDER
        if "market" in text and "closed" in text:
            return BrokerErrorCode.MARKET_CLOSED
        return BrokerErrorCode.BROKER_REJECTED


async def with_http_retry(
    operation: Callable[[], Awaitable[Any]],
    *,
    max_attempts: int = 3,
) -> Any:
    """Lightweight retry for idempotent GET-style calls."""
    last: Exception | None = None
    for attempt in range(1, max_attempts + 1):
        try:
            return await operation()
        except BrokerTransientError as exc:
            last = exc
            if attempt >= max_attempts:
                break
    assert last is not None
    raise last
