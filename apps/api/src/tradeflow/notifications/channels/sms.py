"""SMS notification channel — architecture stub for future Twilio/AWS SNS integration."""

from __future__ import annotations

from tradeflow.notifications.channels.base import ChannelDeliveryResult
from tradeflow.notifications.templates import RenderedNotification


class SmsChannel:
    """
    SMS delivery stub.

    Production integration points:
    - Twilio: POST https://api.twilio.com/2010-04-01/Accounts/{sid}/Messages.json
    - AWS SNS Publish API
    - Config: phone_number in user channel settings, provider credentials in env
    """

    async def send(
        self,
        *,
        config: dict[str, object],
        rendered: RenderedNotification,
    ) -> ChannelDeliveryResult:
        phone = config.get("phone_number")
        if not phone:
            return ChannelDeliveryResult(
                channel="sms",
                success=False,
                error="SMS not configured — set phone_number in channel settings",
            )
        # Architecture-only: log intent without sending until provider is wired.
        return ChannelDeliveryResult(
            channel="sms",
            success=False,
            error="SMS provider not configured (architecture stub)",
        )
