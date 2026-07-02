"""Risk kill switch API integration tests."""

from __future__ import annotations

import pytest
from httpx import AsyncClient
from tests.support.auth_helpers import register_and_login
from tests.support.broker_helpers import connect_paper_account


@pytest.mark.integration
@pytest.mark.api
@pytest.mark.asyncio
async def test_activate_kill_switch_returns_updated_rule(
    client: AsyncClient,
    db_ready,
) -> None:
    await register_and_login(client)
    account_id = await connect_paper_account(
        client,
        account_id="risk-kill-switch-1",
        account_name="Risk Demo",
        connection_name="Risk Paper",
    )

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
