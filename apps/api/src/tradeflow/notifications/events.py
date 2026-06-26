"""Notification event definitions and mappings."""

from __future__ import annotations

from tradeflow.db.enums import NotificationEvent, NotificationType

EVENT_TO_NOTIFICATION_TYPE: dict[NotificationEvent, NotificationType] = {
    NotificationEvent.TRADE_COPIED: NotificationType.TRADE_COPIED,
    NotificationEvent.TRADE_FAILED: NotificationType.COPY_FAILURE,
    NotificationEvent.BROKER_OFFLINE: NotificationType.CONNECTION_LOST,
    NotificationEvent.RISK_ALERT: NotificationType.RISK_BREACH,
    NotificationEvent.SUBSCRIPTION_EXPIRY: NotificationType.BILLING,
    NotificationEvent.PNL_MILESTONE: NotificationType.PNL_MILESTONE,
}

ALL_NOTIFICATION_EVENTS = list(NotificationEvent)
