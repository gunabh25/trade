"""Slack webhook notification channel."""

from __future__ import annotations

import httpx

from tradeflow.core.logging import get_logger
from tradeflow.db.enums import NotificationChannel
from tradeflow.notifications.channels.base import ChannelDeliveryResult
from tradeflow.notifications.templates import RenderedNotification

logger = get_logger(__name__)


class SlackChannel:
    """Posts messages to a Slack incoming webhook."""

    channel = NotificationChannel.SLACK

    async def send(
        self,
        *,
        config: dict[str, object],
        rendered: RenderedNotification,
    ) -> ChannelDeliveryResult:
        webhook_url = config.get("webhook_url")
        if not webhook_url:
            return ChannelDeliveryResult(
                success=False,
                channel=self.channel.value,
                error="slack_webhook_missing",
            )

        payload: dict[str, object] = {
            "text": rendered.slack_text,
            "blocks": rendered.slack_blocks,
        }
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                response = await client.post(str(webhook_url), json=payload)
                response.raise_for_status()
            logger.info("notification_slack_sent")
            return ChannelDeliveryResult(success=True, channel=self.channel.value)
        except Exception as exc:
            logger.error("notification_slack_failed", error=str(exc))
            return ChannelDeliveryResult(
                success=False,
                channel=self.channel.value,
                error=str(exc),
            )
