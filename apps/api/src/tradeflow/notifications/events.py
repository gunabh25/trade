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
    NotificationEvent.LARGE_PROFIT: NotificationType.LARGE_PROFIT,
    NotificationEvent.LARGE_LOSS: NotificationType.LARGE_LOSS,
    NotificationEvent.SYSTEM_MAINTENANCE: NotificationType.SYSTEM,
    NotificationEvent.USER_INVITATION: NotificationType.USER_INVITATION,
    NotificationEvent.PASSWORD_CHANGED: NotificationType.PASSWORD_CHANGED,
}

ALL_NOTIFICATION_EVENTS = list(NotificationEvent)

EVENT_LABELS: dict[NotificationEvent, str] = {
    NotificationEvent.TRADE_COPIED: "Trade Executed",
    NotificationEvent.TRADE_FAILED: "Trade Failed",
    NotificationEvent.BROKER_OFFLINE: "Broker Offline",
    NotificationEvent.RISK_ALERT: "Risk Violation",
    NotificationEvent.SUBSCRIPTION_EXPIRY: "Subscription Expiry",
    NotificationEvent.PNL_MILESTONE: "PnL Milestone",
    NotificationEvent.LARGE_PROFIT: "Large Profit",
    NotificationEvent.LARGE_LOSS: "Large Loss",
    NotificationEvent.SYSTEM_MAINTENANCE: "System Maintenance",
    NotificationEvent.USER_INVITATION: "User Invitation",
    NotificationEvent.PASSWORD_CHANGED: "Password Changed",
}
