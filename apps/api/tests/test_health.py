import pytest
from httpx import ASGITransport, AsyncClient

from tradeflow.core.app_factory import create_app


@pytest.fixture
def app():
    return create_app()


@pytest.fixture
async def client(app):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.mark.asyncio
async def test_root(client: AsyncClient) -> None:
    response = await client.get("/")
    assert response.status_code == 200
    body = response.json()
    assert body["service"] == "TradeFlow AI"
    assert "docs" in body


@pytest.mark.asyncio
async def test_liveness(client: AsyncClient) -> None:
    response = await client.get("/api/v1/health/live")
    assert response.status_code == 200
    body = response.json()
    assert body["data"]["status"] == "alive"
    assert body["data"]["service"] == "TradeFlow AI"
    assert "timestamp" in body["data"]


@pytest.mark.asyncio
async def test_openapi_schema(client: AsyncClient) -> None:
    response = await client.get("/api/openapi.json")
    assert response.status_code == 200
    schema = response.json()
    assert schema["info"]["title"] == "TradeFlow AI"
    assert "/api/v1/health/live" in schema["paths"]
