"""Shared broker helpers for integration tests."""

from __future__ import annotations

from httpx import AsyncClient


async def connect_paper_account(
    client: AsyncClient,
    *,
    account_id: str,
    account_name: str,
    starting_balance: str = "50000",
    connection_name: str | None = None,
) -> str:
    """Connect a paper broker and return the synced trading account id."""
    create = await client.post(
        "/api/v1/broker/connections",
        json={
            "broker": "paper",
            "name": connection_name or account_name,
            "credentials": {
                "account_id": account_id,
                "account_name": account_name,
                "starting_balance": starting_balance,
            },
        },
    )
    assert create.status_code == 200, create.text
    connection_id = create.json()["data"]["id"]

    connect = await client.post(f"/api/v1/broker/connections/{connection_id}/connect")
    assert connect.status_code == 200, connect.text

    accounts = await client.get("/api/v1/broker/trading-accounts")
    assert accounts.status_code == 200, accounts.text
    items = accounts.json()["data"]
    match = next((item for item in items if item["external_account_id"] == account_id), None)
    assert match is not None, f"Paper account {account_id} not found after sync"
    return match["id"]
