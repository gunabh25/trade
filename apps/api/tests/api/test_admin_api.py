"""Admin API endpoint tests."""

from __future__ import annotations

import pytest
from httpx import AsyncClient
from tests.support.auth_helpers import register_and_login

ADMIN_ROUTES = [
    "/api/v1/admin/overview",
    "/api/v1/admin/users",
    "/api/v1/admin/permissions",
    "/api/v1/admin/subscriptions",
    "/api/v1/admin/organizations",
    "/api/v1/admin/trading-accounts",
    "/api/v1/admin/metrics",
    "/api/v1/admin/health",
]


@pytest.mark.api
@pytest.mark.parametrize("path", ADMIN_ROUTES)
@pytest.mark.asyncio
async def test_admin_routes_require_auth(client: AsyncClient, path: str) -> None:
    response = await client.get(path)
    assert response.status_code == 401, f"{path} should require authentication"


@pytest.mark.api
@pytest.mark.integration
@pytest.mark.asyncio
async def test_trader_cannot_access_admin_overview(client: AsyncClient, db_ready) -> None:
    await register_and_login(client)
    response = await client.get("/api/v1/admin/overview")
    assert response.status_code in {403, 401}


@pytest.mark.api
@pytest.mark.asyncio
async def test_admin_search_requires_auth(client: AsyncClient) -> None:
    response = await client.get("/api/v1/admin/search?q=test")
    assert response.status_code == 401
