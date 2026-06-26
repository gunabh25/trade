"""HTTP connection pooling for broker REST adapters."""

from __future__ import annotations

from dataclasses import dataclass, field

import httpx


@dataclass
class BrokerHttpPool:
    """Pooled httpx client per broker base URL."""

    base_url: str
    timeout_seconds: float = 30.0
    max_connections: int = 20
    max_keepalive: int = 10
    _client: httpx.AsyncClient | None = field(default=None, init=False)

    async def get_client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                base_url=self.base_url,
                timeout=httpx.Timeout(self.timeout_seconds),
                limits=httpx.Limits(
                    max_connections=self.max_connections,
                    max_keepalive_connections=self.max_keepalive,
                ),
                follow_redirects=True,
            )
        return self._client

    async def close(self) -> None:
        if self._client is not None and not self._client.is_closed:
            await self._client.aclose()
            self._client = None
