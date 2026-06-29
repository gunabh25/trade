"""API smoke tests — verify every v1 router is mounted and responds correctly."""

from __future__ import annotations

import pytest
from httpx import ASGITransport, AsyncClient

from tradeflow.core.app_factory import create_app

# Public endpoints that must not require authentication
PUBLIC_GET_ENDPOINTS = [
    "/",
    "/api/v1/health/live",
    "/api/v1/health/ready",
    "/api/v1/health/",
    "/metrics",
    "/api/v1/auth/oauth/google",
    "/api/v1/broker/supported",
]

# Authenticated GET endpoints — expect 401 without session
PROTECTED_GET_ENDPOINTS = [
    "/api/v1/auth/me",
    "/api/v1/broker/connections",
    "/api/v1/copy/groups",
    "/api/v1/copy/health",
    "/api/v1/risk/rules",
    "/api/v1/journal/entries",
    "/api/v1/analytics/overview",
    "/api/v1/notifications",
    "/api/v1/billing/overview",
    "/api/v1/billing/invoices",
    "/api/v1/admin/overview",
]

# Admin-only endpoints — expect 401 without session (403 only after auth)
ADMIN_GET_ENDPOINTS = [
    "/api/v1/billing/admin/subscriptions",
    "/api/v1/admin/subscriptions",
    "/api/v1/admin/users",
    "/api/v1/admin/permissions",
]


@pytest.fixture
def app():
    return create_app()


@pytest.fixture
async def client(app):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.mark.asyncio
@pytest.mark.parametrize("path", PUBLIC_GET_ENDPOINTS)
async def test_public_endpoints_respond(client: AsyncClient, path: str) -> None:
    response = await client.get(path, follow_redirects=True)
    allowed = {200, 307, 422, 503}
    assert response.status_code in allowed, f"{path} returned {response.status_code}"


@pytest.mark.asyncio
@pytest.mark.parametrize("path", PROTECTED_GET_ENDPOINTS)
async def test_protected_endpoints_require_auth(client: AsyncClient, path: str) -> None:
    response = await client.get(path)
    assert response.status_code == 401, f"{path} should require auth, got {response.status_code}"


@pytest.mark.asyncio
@pytest.mark.parametrize("path", ADMIN_GET_ENDPOINTS)
async def test_admin_endpoints_require_auth(client: AsyncClient, path: str) -> None:
    response = await client.get(path)
    assert response.status_code == 401, f"{path} should require auth, got {response.status_code}"


@pytest.mark.asyncio
async def test_openapi_lists_all_feature_routers(client: AsyncClient) -> None:
    response = await client.get("/api/openapi.json")
    assert response.status_code == 200
    paths = response.json()["paths"]
    prefixes = [
        "/api/v1/health",
        "/api/v1/auth",
        "/api/v1/broker",
        "/api/v1/copy",
        "/api/v1/risk",
        "/api/v1/journal",
        "/api/v1/analytics",
        "/api/v1/notifications",
        "/api/v1/billing",
        "/api/v1/admin",
    ]
    for prefix in prefixes:
        assert any(p.startswith(prefix) for p in paths), f"No routes for {prefix}"


@pytest.mark.asyncio
async def test_readiness_includes_celery_broker_check(client: AsyncClient) -> None:
    response = await client.get("/api/v1/health/ready")
    body = response.json()
    checks = body["data"]["checks"]
    assert "celery_broker" in checks
    assert checks["celery_broker"]["status"] in {"healthy", "unhealthy", "degraded"}


@pytest.mark.asyncio
async def test_celery_ping_task_eager() -> None:
    from tradeflow.workers.tasks import ping

    result = ping.delay()
    assert result.get(timeout=5) == {"status": "pong"}
