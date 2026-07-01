"""Broker connect and trading account sync integration tests."""

from __future__ import annotations

import pytest
from httpx import AsyncClient
from tests.support.auth_helpers import register_and_login


@pytest.mark.integration
@pytest.mark.api
@pytest.mark.asyncio
async def test_paper_broker_connect_syncs_trading_accounts(
    client: AsyncClient,
    db_ready,
) -> None:
    await register_and_login(client)

    create = await client.post(
        "/api/v1/broker/connections",
        json={
            "broker": "paper",
            "name": "Paper Demo",
            "credentials": {
                "account_id": "paper-onboard-1",
                "account_name": "Onboarding Demo",
                "starting_balance": "25000",
            },
        },
    )
    assert create.status_code == 200, create.text
    connection_id = create.json()["data"]["id"]

    connect = await client.post(f"/api/v1/broker/connections/{connection_id}/connect")
    assert connect.status_code == 200, connect.text
    assert connect.json()["data"]["connected"] is True

    accounts = await client.get("/api/v1/broker/trading-accounts")
    assert accounts.status_code == 200, accounts.text
    items = accounts.json()["data"]
    assert len(items) >= 1
    assert items[0]["external_account_id"] == "paper-onboard-1"
    assert items[0]["name"] == "Onboarding Demo"
