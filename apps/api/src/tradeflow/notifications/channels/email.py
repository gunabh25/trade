"""Email notification channel."""

from __future__ import annotations

import smtplib
from email.message import EmailMessage

from tradeflow.core.config import Settings
from tradeflow.core.logging import get_logger
from tradeflow.db.enums import NotificationChannel
from tradeflow.notifications.channels.base import ChannelDeliveryResult
from tradeflow.notifications.templates import RenderedNotification

logger = get_logger(__name__)


class EmailNotificationChannel:
    """Delivers alert emails via SMTP (logs in dev when SMTP is unset)."""

    channel = NotificationChannel.EMAIL

    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    async def send(
        self,
        *,
        to_email: str,
        rendered: RenderedNotification,
    ) -> ChannelDeliveryResult:
        try:
            if not self._settings.smtp_host:
                logger.info(
                    "notification_email_dev_mode",
                    to=to_email,
                    subject=rendered.email_subject,
                    body=rendered.email_body,
                )
                return ChannelDeliveryResult(success=True, channel=self.channel.value)

            message = EmailMessage()
            message["Subject"] = rendered.email_subject
            message["From"] = self._settings.smtp_from_email
            message["To"] = to_email
            message.set_content(rendered.email_body)

            with smtplib.SMTP(
                self._settings.smtp_host,
                self._settings.smtp_port,
            ) as server:
                server.starttls()
                if self._settings.smtp_user and self._settings.smtp_password:
                    server.login(self._settings.smtp_user, self._settings.smtp_password)
                server.send_message(message)

            logger.info("notification_email_sent", to=to_email)
            return ChannelDeliveryResult(success=True, channel=self.channel.value)
        except Exception as exc:
            logger.error("notification_email_failed", to=to_email, error=str(exc))
            return ChannelDeliveryResult(
                success=False,
                channel=self.channel.value,
                error=str(exc),
            )
