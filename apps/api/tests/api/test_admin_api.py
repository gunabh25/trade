"""Admin API endpoint tests."""

from __future__ import annotations

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from tests.support.auth_helpers import register_and_login
from tests.support.factories import register_payload

from tradeflow.db.enums import RoleName
from tradeflow.db.models.user import Role, User, UserRole

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
@pytest.mark.integration
@pytest.mark.asyncio
async def test_admin_analytics_as_admin(client: AsyncClient, db_ready) -> None:
    payload = register_payload()
    reg = await client.post("/api/v1/auth/register", json=payload)
    assert reg.status_code == 200, reg.text

    login = await client.post(
        "/api/v1/auth/login",
        json={"email": payload["email"], "password": payload["password"]},
    )
    assert login.status_code == 200, login.text

    session_factory = async_sessionmaker(db_ready, class_=AsyncSession, expire_on_commit=False)
    async with session_factory() as db:
        user = await db.scalar(select(User).where(User.email == payload["email"]))
        assert user is not None
        admin_role = await db.scalar(select(Role).where(Role.name == RoleName.ADMIN))
        assert admin_role is not None
        db.add(UserRole(user_id=user.id, role_id=admin_role.id))
        await db.commit()

    login = await client.post(
        "/api/v1/auth/login",
        json={"email": payload["email"], "password": payload["password"]},
    )
    assert login.status_code == 200, login.text
    csrf = login.json().get("data", {}).get("csrf_token")
    if csrf:
        client.headers["X-CSRF-Token"] = csrf

    response = await client.get("/api/v1/admin/analytics")
    assert response.status_code == 200, response.text
    body = response.json()
    assert "data" in body
    assert "users_by_month" in body["data"]


@pytest.mark.api
@pytest.mark.asyncio
async def test_admin_search_requires_auth(client: AsyncClient) -> None:
    response = await client.get("/api/v1/admin/search?q=test")
    assert response.status_code == 401
