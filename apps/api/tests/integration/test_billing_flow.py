"""Billing integration tests against live API + database."""

from __future__ import annotations

import pytest
from httpx import AsyncClient
from tests.support.auth_helpers import register_and_login


@pytest.mark.integration
@pytest.mark.api
@pytest.mark.asyncio
async def test_billing_plans_public(client: AsyncClient, db_ready) -> None:
    response = await client.get("/api/v1/billing/plans")
    assert response.status_code == 200
    body = response.json()
    assert "data" in body


@pytest.mark.integration
@pytest.mark.api
@pytest.mark.asyncio
async def test_billing_overview_requires_auth(client: AsyncClient) -> None:
    response = await client.get("/api/v1/billing/overview")
    assert response.status_code == 401


@pytest.mark.integration
@pytest.mark.api
@pytest.mark.asyncio
async def test_authenticated_billing_overview(client: AsyncClient, db_ready) -> None:
    await register_and_login(client)
    response = await client.get("/api/v1/billing/overview")
    assert response.status_code == 200
    body = response.json()
    assert "data" in body


@pytest.mark.integration
@pytest.mark.api
@pytest.mark.asyncio
async def test_authenticated_invoices_list(client: AsyncClient, db_ready) -> None:
    await register_and_login(client)
    response = await client.get("/api/v1/billing/invoices")
    assert response.status_code == 200
