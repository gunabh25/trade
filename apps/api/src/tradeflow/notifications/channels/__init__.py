"""Notification channel adapters."""

from tradeflow.notifications.channels.base import ChannelDeliveryResult
from tradeflow.notifications.channels.discord import DiscordChannel
from tradeflow.notifications.channels.email import EmailNotificationChannel
from tradeflow.notifications.channels.push import PushChannel
from tradeflow.notifications.channels.slack import SlackChannel
from tradeflow.notifications.channels.telegram import TelegramChannel

__all__ = [
    "ChannelDeliveryResult",
    "DiscordChannel",
    "EmailNotificationChannel",
    "PushChannel",
    "SlackChannel",
    "TelegramChannel",
]
