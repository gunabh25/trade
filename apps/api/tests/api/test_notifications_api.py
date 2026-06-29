"""Notifications API tests."""

from __future__ import annotations

import pytest
from httpx import AsyncClient
from tests.support.auth_helpers import register_and_login


@pytest.mark.api
@pytest.mark.asyncio
async def test_notifications_list_requires_auth(client: AsyncClient) -> None:
    response = await client.get("/api/v1/notifications")
    assert response.status_code == 401


@pytest.mark.api
@pytest.mark.integration
@pytest.mark.asyncio
async def test_authenticated_notifications_list(client: AsyncClient, db_ready) -> None:
    await register_and_login(client)
    response = await client.get("/api/v1/notifications")
    assert response.status_code == 200
    body = response.json()
    assert "data" in body


@pytest.mark.api
@pytest.mark.integration
@pytest.mark.asyncio
async def test_notification_preferences_requires_auth(client: AsyncClient) -> None:
    response = await client.get("/api/v1/notifications/preferences")
    assert response.status_code == 401


@pytest.mark.api
@pytest.mark.integration
@pytest.mark.asyncio
async def test_authenticated_notification_preferences(client: AsyncClient, db_ready) -> None:
    await register_and_login(client)
    response = await client.get("/api/v1/notifications/preferences")
    assert response.status_code == 200
