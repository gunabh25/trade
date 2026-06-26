"""Notification templates for in-app and external channels."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from tradeflow.core.config import Settings
from tradeflow.db.enums import NotificationEvent


@dataclass(frozen=True)
class RenderedNotification:
    """Channel-ready notification content."""

    title: str
    body: str
    action_url: str | None
    email_subject: str
    email_body: str
    telegram_text: str
    discord_embed: dict[str, Any]
    slack_text: str
    slack_blocks: list[dict[str, Any]]
    push_title: str
    push_body: str


def _dashboard_url(settings: Settings, path: str) -> str:
    base = settings.frontend_url.rstrip("/")
    return f"{base}{path}"


def render_notification(
    settings: Settings,
    event: NotificationEvent,
    payload: dict[str, Any],
) -> RenderedNotification:
    """Build notification content for all supported channels."""
    renderers = {
        NotificationEvent.TRADE_COPIED: _trade_copied,
        NotificationEvent.TRADE_FAILED: _trade_failed,
        NotificationEvent.BROKER_OFFLINE: _broker_offline,
        NotificationEvent.RISK_ALERT: _risk_alert,
        NotificationEvent.SUBSCRIPTION_EXPIRY: _subscription_expiry,
        NotificationEvent.PNL_MILESTONE: _pnl_milestone,
    }
    renderer = renderers.get(event)
    if renderer is None:
        msg = f"Unknown notification event: {event}"
        raise ValueError(msg)
    return renderer(settings, payload)


def _trade_copied(settings: Settings, payload: dict[str, Any]) -> RenderedNotification:
    symbol = str(payload.get("symbol", "—"))
    action = str(payload.get("action", "copy")).replace("_", " ").title()
    latency = payload.get("latency_ms")
    latency_text = f" ({latency}ms)" if latency is not None else ""
    title = f"Trade Copied: {symbol}"
    body = f"{action} copied to follower account{latency_text}."
    action_url = "/dashboard/copy"
    return _build(
        settings,
        title=title,
        body=body,
        action_url=action_url,
        accent_color=0x22C55E,
        emoji="✅",
    )


def _trade_failed(settings: Settings, payload: dict[str, Any]) -> RenderedNotification:
    symbol = str(payload.get("symbol", "—"))
    error = str(payload.get("error", "Unknown error"))
    title = f"Copy Failed: {symbol}"
    body = f"Trade copy failed — {error}"
    action_url = "/dashboard/copy"
    return _build(
        settings,
        title=title,
        body=body,
        action_url=action_url,
        accent_color=0xEF4444,
        emoji="❌",
    )


def _broker_offline(settings: Settings, payload: dict[str, Any]) -> RenderedNotification:
    broker = str(payload.get("broker", "Broker"))
    connection = str(payload.get("connection_name", "Connection"))
    title = f"Broker Offline: {broker}"
    body = f"{connection} is disconnected. Copy trading may be paused."
    action_url = "/dashboard/accounts"
    return _build(
        settings,
        title=title,
        body=body,
        action_url=action_url,
        accent_color=0xF59E0B,
        emoji="⚠️",
    )


def _risk_alert(settings: Settings, payload: dict[str, Any]) -> RenderedNotification:
    breach = str(payload.get("breach_type", "Risk limit")).replace("_", " ").title()
    message = str(payload.get("message", "A risk rule was breached."))
    account_id = payload.get("account_id")
    action_url = f"/dashboard/risk?account={account_id}" if account_id else "/dashboard/risk"
    title = f"Risk Alert: {breach}"
    body = message
    return _build(
        settings,
        title=title,
        body=body,
        action_url=action_url,
        accent_color=0xDC2626,
        emoji="🚨",
    )


def _subscription_expiry(settings: Settings, payload: dict[str, Any]) -> RenderedNotification:
    plan = str(payload.get("plan_name", "Pro"))
    days = payload.get("days_remaining")
    days_text = f" in {days} day(s)" if days is not None else " soon"
    title = "Subscription Expiring"
    body = f"Your {plan} plan expires{days_text}. Renew to keep premium features."
    action_url = "/dashboard/billing"
    return _build(
        settings,
        title=title,
        body=body,
        action_url=action_url,
        accent_color=0x8B5CF6,
        emoji="💳",
    )


def _pnl_milestone(settings: Settings, payload: dict[str, Any]) -> RenderedNotification:
    milestone = str(payload.get("milestone_label", "Milestone"))
    pnl = payload.get("pnl")
    pnl_text = f" (${pnl:,.2f})" if isinstance(pnl, (int, float)) else ""
    title = f"PnL Milestone: {milestone}"
    body = f"You reached {milestone}{pnl_text}. Keep up the momentum!"
    action_url = "/dashboard/analytics"
    return _build(
        settings,
        title=title,
        body=body,
        action_url=action_url,
        accent_color=0x3B82F6,
        emoji="📈",
    )


def _build(
    settings: Settings,
    *,
    title: str,
    body: str,
    action_url: str,
    accent_color: int,
    emoji: str,
) -> RenderedNotification:
    full_url = _dashboard_url(settings, action_url)
    email_body = f"{body}\n\nOpen TradeFlow AI: {full_url}"
    telegram_text = f"{emoji} *{title}*\n{body}\n\n[Open dashboard]({full_url})"
    discord_embed = {
        "title": f"{emoji} {title}",
        "description": body,
        "color": accent_color,
        "url": full_url,
    }
    slack_text = f"{emoji} *{title}*\n{body}\n<{full_url}|Open dashboard>"
    slack_blocks = [
        {
            "type": "section",
            "text": {"type": "mrkdwn", "text": slack_text},
        },
    ]
    return RenderedNotification(
        title=title,
        body=body,
        action_url=action_url,
        email_subject=f"TradeFlow AI — {title}",
        email_body=email_body,
        telegram_text=telegram_text,
        discord_embed=discord_embed,
        slack_text=slack_text,
        slack_blocks=slack_blocks,
        push_title=title,
        push_body=body,
    )
