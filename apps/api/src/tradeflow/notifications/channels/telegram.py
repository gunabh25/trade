"""Telegram notification channel."""

from __future__ import annotations

import httpx

from tradeflow.core.config import Settings
from tradeflow.core.logging import get_logger
from tradeflow.db.enums import NotificationChannel
from tradeflow.notifications.channels.base import ChannelDeliveryResult
from tradeflow.notifications.templates import RenderedNotification

logger = get_logger(__name__)


class TelegramChannel:
    """Sends messages via Telegram Bot API."""

    channel = NotificationChannel.TELEGRAM

    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    async def send(
        self,
        *,
        config: dict[str, object],
        rendered: RenderedNotification,
    ) -> ChannelDeliveryResult:
        bot_token = config.get("bot_token") or self._settings.telegram_bot_token
        chat_id = config.get("chat_id")
        if not bot_token or not chat_id:
            return ChannelDeliveryResult(
                success=False,
                channel=self.channel.value,
                error="telegram_not_configured",
            )

        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        payload = {
            "chat_id": str(chat_id),
            "text": rendered.telegram_text,
            "parse_mode": "Markdown",
            "disable_web_page_preview": False,
        }
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                response = await client.post(url, json=payload)
                response.raise_for_status()
            logger.info("notification_telegram_sent", chat_id=str(chat_id))
            return ChannelDeliveryResult(success=True, channel=self.channel.value)
        except Exception as exc:
            logger.error("notification_telegram_failed", error=str(exc))
            return ChannelDeliveryResult(
                success=False,
                channel=self.channel.value,
                error=str(exc),
            )
