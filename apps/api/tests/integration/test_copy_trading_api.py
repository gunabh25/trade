"""Copy trading API integration tests."""

from __future__ import annotations

import pytest
from httpx import AsyncClient
from tests.support.auth_helpers import register_and_login
from tests.support.broker_helpers import connect_paper_account


@pytest.mark.integration
@pytest.mark.api
@pytest.mark.asyncio
async def test_copy_group_simulate_event_replicates_to_follower(
    client: AsyncClient,
    db_ready,
) -> None:
    await register_and_login(client)

    leader_account_id = await connect_paper_account(
        client,
        account_id="copy-leader-1",
        account_name="Copy Leader",
        connection_name="Leader Connection",
    )
    follower_account_id = await connect_paper_account(
        client,
        account_id="copy-follower-1",
        account_name="Copy Follower",
        connection_name="Follower Connection",
    )

    create_group = await client.post(
        "/api/v1/copy/groups",
        json={
            "name": "Paper Beta Group",
            "leader_account_id": leader_account_id,
            "mode": "live",
        },
    )
    assert create_group.status_code == 200, create_group.text
    group_id = create_group.json()["data"]["id"]

    add_follower = await client.post(
        f"/api/v1/copy/groups/{group_id}/followers",
        json={
            "follower_account_id": follower_account_id,
            "copy_mode": "fixed_quantity",
            "sizing_value": "1",
        },
    )
    assert add_follower.status_code == 200, add_follower.text

    start = await client.post(f"/api/v1/copy/groups/{group_id}/start")
    assert start.status_code == 200, start.text
    assert start.json()["data"]["copying_enabled"] is True

    simulate = await client.post(
        f"/api/v1/copy/groups/{group_id}/simulate",
        json={
            "symbol": "ES",
            "side": "buy",
            "quantity": 1,
        },
    )
    assert simulate.status_code == 200, simulate.text
    results = simulate.json()["data"]
    assert len(results) >= 1
    assert results[0]["success"] is True

    logs = await client.get(f"/api/v1/copy/groups/{group_id}/execution-logs")
    assert logs.status_code == 200, logs.text
    assert len(logs.json()["data"]) >= 1

    events = await client.get(f"/api/v1/copy/groups/{group_id}/events")
    assert events.status_code == 200, events.text
    assert len(events.json()["data"]) >= 1

    health = await client.get("/api/v1/copy/health")
    assert health.status_code == 200, health.text
    assert health.json()["data"]["active_groups"] >= 1
