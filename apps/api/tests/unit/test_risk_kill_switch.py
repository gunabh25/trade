"""Kill switch and risk notification unit tests."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from tradeflow.core.config import get_settings
from tradeflow.db.enums import NotificationEvent, NotificationType
from tradeflow.db.models.notification import Notification
from tradeflow.notifications.dispatcher import NotificationDispatcher
from tradeflow.risk.alerts import RiskAlertService
from tradeflow.risk.state import RiskStateStore


@pytest.mark.unit
@pytest.mark.asyncio
async def test_dispatch_risk_alert_with_string_notification_type(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """ORM string columns may return plain strings after flush — dispatch must not crash."""
    delay = MagicMock()
    monkeypatch.setattr(
        "tradeflow.workers.notification_tasks.deliver_notification_channels",
        MagicMock(delay=delay),
    )

    settings = get_settings()
    redis = AsyncMock()
    dispatcher = NotificationDispatcher(settings, redis)

    db = AsyncMock()
    db.get = AsyncMock(return_value=None)
    db.scalars = AsyncMock(return_value=MagicMock(all=MagicMock(return_value=[])))

    stored: list[Notification] = []

    def _capture_notification(model: Notification) -> None:
        model.id = uuid4()
        stored.append(model)

    db.add = MagicMock(side_effect=_capture_notification)

    async def _flush_sets_string_type() -> None:
        for model in stored:
            model.type = "risk_breach"

    db.flush = AsyncMock(side_effect=_flush_sets_string_type)

    await dispatcher.dispatch(
        db,
        user_id=uuid4(),
        event=NotificationEvent.RISK_ALERT,
        payload={"breach_type": "kill_switch", "message": "halted"},
    )

    redis.publish.assert_awaited()
    published = redis.publish.await_args.args[1]
    assert "risk_breach" in published


@pytest.mark.unit
@pytest.mark.asyncio
async def test_send_kill_switch_alert_updates_notification_type() -> None:
    """Kill switch alerts re-type the in-app notification after dispatch."""
    state_store = AsyncMock(spec=RiskStateStore)
    state_store.publish_status = AsyncMock()

    dispatcher = AsyncMock()
    notification = Notification(
        id=uuid4(),
        user_id=uuid4(),
        type=NotificationType.RISK_BREACH,
        title="Risk Alert",
        body="body",
    )
    dispatcher.notify_risk_alert = AsyncMock(return_value=notification)

    alerts = RiskAlertService(state_store, notification_dispatcher=dispatcher)
    db = AsyncMock()
    db.flush = AsyncMock()

    user_id = uuid4()
    account_id = uuid4()
    result = await alerts.send_kill_switch_alert(
        db,
        user_id=user_id,
        account_id=account_id,
        activated=True,
    )

    assert result.type == NotificationType.KILL_SWITCH
    assert result.title == "Kill Switch Activated"
    dispatcher.notify_risk_alert.assert_awaited_once()
    state_store.publish_status.assert_awaited_once()
