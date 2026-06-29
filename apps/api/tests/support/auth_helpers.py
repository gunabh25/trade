"""Authentication helpers for API integration tests."""

from __future__ import annotations

from httpx import AsyncClient

from tests.support.factories import register_payload


async def register_and_login(client: AsyncClient) -> dict[str, str]:
    """Register a user, log in, and attach CSRF header for mutating requests."""
    payload = register_payload()
    reg = await client.post("/api/v1/auth/register", json=payload)
    assert reg.status_code == 200, reg.text

    login = await client.post(
        "/api/v1/auth/login",
        json={"email": payload["email"], "password": payload["password"]},
    )
    assert login.status_code == 200, login.text

    login_body = login.json()
    csrf = login_body.get("data", {}).get("csrf_token")
    if csrf:
        client.headers["X-CSRF-Token"] = csrf

    return payload


async def auth_headers(client: AsyncClient) -> dict[str, str]:
    """Ensure authenticated session; return CSRF header if present."""
    await register_and_login(client)
    csrf = client.headers.get("X-CSRF-Token")
    if csrf:
        return {"X-CSRF-Token": csrf}
    return {}


async def get_me(client: AsyncClient) -> dict[str, object]:
    response = await client.get("/api/v1/auth/me")
    assert response.status_code == 200, response.text
    body = response.json()
    return body["data"]  # type: ignore[return-value]
