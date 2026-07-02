"""Risk kill switch API integration tests."""

from __future__ import annotations

import pytest
from httpx import AsyncClient
from tests.support.auth_helpers import register_and_login


async def _connect_paper_account(client: AsyncClient) -> str:
    create = await client.post(
        "/api/v1/broker/connections",
        json={
            "broker": "paper",
            "name": "Risk Paper",
            "credentials": {
                "account_id": "risk-kill-switch-1",
                "account_name": "Risk Demo",
                "starting_balance": "50000",
            },
        },
    )
    assert create.status_code == 200, create.text
    connection_id = create.json()["data"]["id"]

    connect = await client.post(f"/api/v1/broker/connections/{connection_id}/connect")
    assert connect.status_code == 200, connect.text

    accounts = await client.get("/api/v1/broker/trading-accounts")
    assert accounts.status_code == 200, accounts.text
    account_id = accounts.json()["data"][0]["id"]
    return account_id


@pytest.mark.integration
@pytest.mark.api
@pytest.mark.asyncio
async def test_activate_kill_switch_returns_updated_rule(
    client: AsyncClient,
    db_ready,
) -> None:
    await register_and_login(client)
    account_id = await _connect_paper_account(client)

    create_rule = await client.post(
        "/api/v1/risk/rules",
        json={
            "trading_account_id": account_id,
            "name": "Default",
            "enabled": True,
            "auto_flatten_on_breach": True,
            "auto_stop_copying_on_breach": True,
        },
    )
    assert create_rule.status_code == 200, create_rule.text
    rule_id = create_rule.json()["data"]["id"]

    activate = await client.post(f"/api/v1/risk/rules/{rule_id}/kill-switch/activate")
    assert activate.status_code == 200, activate.text
    body = activate.json()["data"]
    assert body["kill_switch_active"] is True

    deactivate = await client.post(f"/api/v1/risk/rules/{rule_id}/kill-switch/deactivate")
    assert deactivate.status_code == 200, deactivate.text
    assert deactivate.json()["data"]["kill_switch_active"] is False
