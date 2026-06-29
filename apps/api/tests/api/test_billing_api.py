"""Billing API route tests."""

from __future__ import annotations

import pytest
from httpx import AsyncClient


@pytest.mark.api
@pytest.mark.asyncio
async def test_billing_admin_subscriptions_requires_auth(client: AsyncClient) -> None:
    response = await client.get("/api/v1/billing/admin/subscriptions")
    assert response.status_code == 401


@pytest.mark.api
@pytest.mark.asyncio
async def test_billing_checkout_requires_auth(client: AsyncClient) -> None:
    response = await client.post(
        "/api/v1/billing/checkout",
        json={"plan_code": "pro"},
    )
    assert response.status_code == 401
