"""Notification template and event mapping tests."""

from __future__ import annotations

from tradeflow.core.config import get_settings
from tradeflow.db.enums import NotificationEvent, NotificationType
from tradeflow.notifications.events import EVENT_TO_NOTIFICATION_TYPE
from tradeflow.notifications.templates import render_notification


def test_all_events_map_to_notification_types() -> None:
    for event in NotificationEvent:
        assert event in EVENT_TO_NOTIFICATION_TYPE
        assert isinstance(EVENT_TO_NOTIFICATION_TYPE[event], NotificationType)


def test_trade_copied_template() -> None:
    settings = get_settings()
    rendered = render_notification(
        settings,
        NotificationEvent.TRADE_COPIED,
        {"symbol": "ES", "action": "place", "latency_ms": 42},
    )
    assert "ES" in rendered.title
    assert "Place" in rendered.body
    assert rendered.email_subject.startswith("TradeFlow AI")
    assert rendered.discord_embed["color"] == 0x22C55E
    assert "ES" in rendered.push_title


def test_trade_failed_template() -> None:
    settings = get_settings()
    rendered = render_notification(
        settings,
        NotificationEvent.TRADE_FAILED,
        {"symbol": "NQ", "error": "insufficient margin"},
    )
    assert "NQ" in rendered.title
    assert "insufficient margin" in rendered.body
    assert rendered.discord_embed["color"] == 0xEF4444


def test_broker_offline_template() -> None:
    settings = get_settings()
    rendered = render_notification(
        settings,
        NotificationEvent.BROKER_OFFLINE,
        {"broker": "Paper", "connection_name": "Demo Account"},
    )
    assert "Paper" in rendered.title
    assert "Demo Account" in rendered.body


def test_risk_alert_template() -> None:
    settings = get_settings()
    rendered = render_notification(
        settings,
        NotificationEvent.RISK_ALERT,
        {
            "breach_type": "daily_loss",
            "message": "Daily loss limit exceeded",
            "account_id": "abc-123",
        },
    )
    assert "Daily Loss" in rendered.title
    assert "Daily loss limit exceeded" in rendered.body


def test_subscription_expiry_template() -> None:
    settings = get_settings()
    rendered = render_notification(
        settings,
        NotificationEvent.SUBSCRIPTION_EXPIRY,
        {"plan_name": "Pro", "days_remaining": 3},
    )
    assert "Subscription Expiring" in rendered.title
    assert "Pro" in rendered.body
    assert "3" in rendered.body


def test_pnl_milestone_template() -> None:
    settings = get_settings()
    rendered = render_notification(
        settings,
        NotificationEvent.PNL_MILESTONE,
        {"milestone_label": "$100,000 equity", "pnl": 100_500.25},
    )
    assert "$100,000 equity" in rendered.title
    assert "100,500.25" in rendered.body
