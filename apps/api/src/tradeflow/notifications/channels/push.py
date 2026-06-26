"""Web push notification channel (logs in dev; POST when endpoint configured)."""

from __future__ import annotations

import httpx

from tradeflow.core.logging import get_logger
from tradeflow.db.enums import NotificationChannel
from tradeflow.notifications.channels.base import ChannelDeliveryResult
from tradeflow.notifications.templates import RenderedNotification

logger = get_logger(__name__)


class PushChannel:
    """Delivers push notifications via configured endpoint or dev log."""

    channel = NotificationChannel.PUSH

    async def send(
        self,
        *,
        config: dict[str, object],
        rendered: RenderedNotification,
    ) -> ChannelDeliveryResult:
        endpoint = config.get("endpoint")
        if not endpoint:
            logger.info(
                "notification_push_dev_mode",
                title=rendered.push_title,
                body=rendered.push_body,
            )
            return ChannelDeliveryResult(success=True, channel=self.channel.value)

        payload = {
            "title": rendered.push_title,
            "body": rendered.push_body,
            "data": {"url": rendered.action_url},
        }
        headers: dict[str, str] = {}
        auth = config.get("auth_header")
        if auth:
            headers["Authorization"] = str(auth)

        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                response = await client.post(str(endpoint), json=payload, headers=headers)
                response.raise_for_status()
            logger.info("notification_push_sent")
            return ChannelDeliveryResult(success=True, channel=self.channel.value)
        except Exception as exc:
            logger.error("notification_push_failed", error=str(exc))
            return ChannelDeliveryResult(
                success=False,
                channel=self.channel.value,
                error=str(exc),
            )
