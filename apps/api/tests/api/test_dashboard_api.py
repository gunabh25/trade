"""Dashboard / analytics API tests."""

from __future__ import annotations

import pytest
from httpx import AsyncClient
from tests.support.auth_helpers import register_and_login

DASHBOARD_ROUTES = [
    "/api/v1/analytics/overview",
    "/api/v1/copy/groups",
    "/api/v1/copy/health",
    "/api/v1/risk/rules",
]


@pytest.mark.api
@pytest.mark.parametrize("path", DASHBOARD_ROUTES)
@pytest.mark.asyncio
async def test_dashboard_routes_require_auth(client: AsyncClient, path: str) -> None:
    response = await client.get(path)
    assert response.status_code == 401


@pytest.mark.api
@pytest.mark.integration
@pytest.mark.asyncio
async def test_analytics_overview_for_authenticated_user(
    client: AsyncClient,
    db_ready,
) -> None:
    await register_and_login(client)
    response = await client.get("/api/v1/analytics/overview")
    assert response.status_code == 200
    body = response.json()
    assert "data" in body


@pytest.mark.api
@pytest.mark.integration
@pytest.mark.asyncio
async def test_copy_health_for_authenticated_user(client: AsyncClient, db_ready) -> None:
    await register_and_login(client)
    response = await client.get("/api/v1/copy/health")
    assert response.status_code == 200
