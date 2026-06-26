"""Admin portal schema and auth tests."""

from __future__ import annotations

from httpx import ASGITransport, AsyncClient

from tradeflow.core.app_factory import create_app
from tradeflow.features.admin.schemas import AdminOverviewResponse, AdminPermissionsResponse


def test_admin_overview_schema() -> None:
    overview = AdminOverviewResponse(
        total_users=100,
        active_users=80,
        total_subscriptions=50,
        active_subscriptions=40,
        open_tickets=3,
        broker_connections=120,
        broker_errors=2,
        published_announcements=1,
        enabled_feature_flags=5,
    )
    assert overview.total_users == 100
    assert overview.enabled_feature_flags == 5


def test_admin_permissions_schema() -> None:
    perms = AdminPermissionsResponse(
        roles=["admin", "support", "trader"],
        permissions={
            "admin": ["users:read", "users:write"],
            "support": ["tickets:read"],
            "trader": [],
        },
    )
    assert "admin" in perms.roles
    assert "users:write" in perms.permissions["admin"]


async def test_admin_overview_requires_authentication() -> None:
    app = create_app()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        response = await client.get("/api/v1/admin/overview")
    assert response.status_code == 401


async def test_admin_search_requires_authentication() -> None:
    app = create_app()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        response = await client.get("/api/v1/admin/search?q=test")
    assert response.status_code == 401
