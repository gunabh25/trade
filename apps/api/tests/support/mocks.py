"""Mock external services for isolated tests."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any
from unittest.mock import AsyncMock, MagicMock


@dataclass
class MockEmailService:
    sent: list[dict[str, Any]] = field(default_factory=list)

    async def send_password_reset(self, *, to: str, reset_url: str) -> None:
        self.sent.append({"type": "password_reset", "to": to, "reset_url": reset_url})

    async def send_verification(self, *, to: str, verify_url: str) -> None:
        self.sent.append({"type": "verification", "to": to, "verify_url": verify_url})


@dataclass
class MockStripeClient:
    enabled: bool = False
    customers: dict[str, str] = field(default_factory=dict)
    checkout_sessions: list[dict[str, Any]] = field(default_factory=list)

    def create_customer(self, *, email: str, name: str | None = None) -> str:
        customer_id = f"cus_mock_{len(self.customers)}"
        self.customers[customer_id] = email
        return customer_id

    def create_checkout_session(self, **kwargs: Any) -> str:
        self.checkout_sessions.append(kwargs)
        return "https://checkout.stripe.test/session/mock"


def mock_broker_adapter(*, connected: bool = True) -> MagicMock:
    adapter = MagicMock()
    adapter.connect = AsyncMock()
    adapter.disconnect = AsyncMock()
    adapter.fetch_accounts = AsyncMock(return_value=[])
    adapter.fetch_orders = AsyncMock(return_value=[])
    adapter.fetch_positions = AsyncMock(return_value=[])
    health = MagicMock()
    health.connected = connected
    health.latency_ms = 12.5
    health.last_error = None
    adapter.get_health = MagicMock(return_value=health)
    return adapter


def mock_redis_pipeline() -> AsyncMock:
    pipe = AsyncMock()
    pipe.execute = AsyncMock(return_value=[])
    return pipe
