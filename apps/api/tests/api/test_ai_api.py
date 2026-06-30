"""API tests for AI endpoints."""

from __future__ import annotations

import pytest
from httpx import AsyncClient


@pytest.mark.api
@pytest.mark.asyncio
async def test_ai_status_requires_auth(client: AsyncClient) -> None:
    response = await client.get("/api/v1/ai/status")
    assert response.status_code == 401


@pytest.mark.api
@pytest.mark.asyncio
async def test_ai_chat(authenticated_client: AsyncClient) -> None:
    response = await authenticated_client.post(
        "/api/v1/ai/chat",
        json={"message": "Summarize my recent trading activity"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["data"]["content"]


@pytest.mark.api
@pytest.mark.asyncio
async def test_ai_trade_summarize(authenticated_client: AsyncClient) -> None:
    response = await authenticated_client.post("/api/v1/ai/trade/summarize", json={})
    assert response.status_code == 200
    assert response.json()["data"]["content"]


@pytest.mark.api
@pytest.mark.asyncio
async def test_ai_risk_analyze(authenticated_client: AsyncClient) -> None:
    response = await authenticated_client.post("/api/v1/ai/risk/analyze", json={})
    assert response.status_code == 200


@pytest.mark.api
@pytest.mark.asyncio
async def test_ai_journal_patterns(authenticated_client: AsyncClient) -> None:
    response = await authenticated_client.post("/api/v1/ai/journal/patterns", json={})
    assert response.status_code == 200
