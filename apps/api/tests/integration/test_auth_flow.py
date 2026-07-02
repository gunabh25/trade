"""Authentication integration tests (register → login → me)."""

from __future__ import annotations

import pytest
from httpx import AsyncClient
from tests.support.auth_helpers import get_me, register_and_login
from tests.support.factories import register_payload, unique_email


@pytest.mark.integration
@pytest.mark.api
@pytest.mark.asyncio
async def test_update_profile(client: AsyncClient, db_ready) -> None:
    await register_and_login(client)

    patch = await client.patch(
        "/api/v1/auth/me",
        json={"first_name": "Updated", "last_name": "Trader", "bio": "Paper beta"},
    )
    assert patch.status_code == 200, patch.text
    body = patch.json()["data"]
    assert body["first_name"] == "Updated"
    assert body["last_name"] == "Trader"
    assert body["bio"] == "Paper beta"

    me = await get_me(client)
    assert me["first_name"] == "Updated"
    assert me["bio"] == "Paper beta"


@pytest.mark.integration
@pytest.mark.api
@pytest.mark.asyncio
async def test_register_login_and_me_flow(client: AsyncClient, db_ready) -> None:
    payload = await register_and_login(client)
    me = await get_me(client)
    assert me["email"] == payload["email"]
    assert me["first_name"] == payload["first_name"]


@pytest.mark.integration
@pytest.mark.api
@pytest.mark.asyncio
async def test_duplicate_registration_rejected(client: AsyncClient, db_ready) -> None:
    email = unique_email("dup")
    payload = register_payload(email=email)
    first = await client.post("/api/v1/auth/register", json=payload)
    assert first.status_code == 200

    second = await client.post("/api/v1/auth/register", json=payload)
    assert second.status_code == 409


@pytest.mark.integration
@pytest.mark.api
@pytest.mark.asyncio
async def test_login_invalid_password_returns_401(client: AsyncClient, db_ready) -> None:
    payload = register_payload()
    await client.post("/api/v1/auth/register", json=payload)

    bad_login = await client.post(
        "/api/v1/auth/login",
        json={"email": payload["email"], "password": "WrongPass9"},
    )
    assert bad_login.status_code == 401


@pytest.mark.integration
@pytest.mark.api
@pytest.mark.asyncio
async def test_logout_clears_session(client: AsyncClient, db_ready) -> None:
    await register_and_login(client)
    logout = await client.post("/api/v1/auth/logout")
    assert logout.status_code == 200

    me = await client.get("/api/v1/auth/me")
    assert me.status_code == 401
