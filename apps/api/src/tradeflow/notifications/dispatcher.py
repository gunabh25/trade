"""Central notification dispatcher — in-app persistence + multi-channel delivery."""

from __future__ import annotations

import json
from typing import Any
from uuid import UUID

from redis.asyncio import Redis
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from tradeflow.core.config import Settings
from tradeflow.core.logging import get_logger
from tradeflow.db.enums import NotificationChannel, NotificationEvent
from tradeflow.db.models.notification import Notification
from tradeflow.db.models.notification_platform import (
    NotificationDelivery,
    NotificationDigestItem,
    NotificationUserSettings,
)
from tradeflow.db.models.notification_settings import (
    NotificationChannelSetting,
    NotificationPreference,
)
from tradeflow.db.models.user import User
from tradeflow.notifications.channels.discord import DiscordChannel
from tradeflow.notifications.channels.email import EmailNotificationChannel
from tradeflow.notifications.channels.push import PushChannel
from tradeflow.notifications.channels.slack import SlackChannel
from tradeflow.notifications.channels.sms import SmsChannel
from tradeflow.notifications.channels.telegram import TelegramChannel
from tradeflow.notifications.events import EVENT_TO_NOTIFICATION_TYPE
from tradeflow.notifications.templates import RenderedNotification, render_notification

logger = get_logger(__name__)

DEFAULT_EVENT_CHANNELS: dict[NotificationEvent, set[NotificationChannel]] = {
    NotificationEvent.TRADE_COPIED: {
        NotificationChannel.IN_APP,
        NotificationChannel.PUSH,
    },
    NotificationEvent.TRADE_FAILED: {
        NotificationChannel.IN_APP,
        NotificationChannel.EMAIL,
        NotificationChannel.TELEGRAM,
        NotificationChannel.DISCORD,
        NotificationChannel.SLACK,
        NotificationChannel.PUSH,
    },
    NotificationEvent.BROKER_OFFLINE: {
        NotificationChannel.IN_APP,
        NotificationChannel.EMAIL,
        NotificationChannel.TELEGRAM,
        NotificationChannel.DISCORD,
        NotificationChannel.SLACK,
        NotificationChannel.PUSH,
    },
    NotificationEvent.RISK_ALERT: {
        NotificationChannel.IN_APP,
        NotificationChannel.EMAIL,
        NotificationChannel.TELEGRAM,
        NotificationChannel.DISCORD,
        NotificationChannel.SLACK,
        NotificationChannel.PUSH,
    },
    NotificationEvent.SUBSCRIPTION_EXPIRY: {
        NotificationChannel.IN_APP,
        NotificationChannel.EMAIL,
        NotificationChannel.PUSH,
    },
    NotificationEvent.PNL_MILESTONE: {
        NotificationChannel.IN_APP,
        NotificationChannel.EMAIL,
        NotificationChannel.PUSH,
    },
    NotificationEvent.LARGE_PROFIT: {
        NotificationChannel.IN_APP,
        NotificationChannel.EMAIL,
        NotificationChannel.TELEGRAM,
        NotificationChannel.PUSH,
    },
    NotificationEvent.LARGE_LOSS: {
        NotificationChannel.IN_APP,
        NotificationChannel.EMAIL,
        NotificationChannel.TELEGRAM,
        NotificationChannel.DISCORD,
        NotificationChannel.SLACK,
        NotificationChannel.PUSH,
    },
    NotificationEvent.SYSTEM_MAINTENANCE: {
        NotificationChannel.IN_APP,
        NotificationChannel.EMAIL,
        NotificationChannel.PUSH,
    },
    NotificationEvent.USER_INVITATION: {
        NotificationChannel.IN_APP,
        NotificationChannel.EMAIL,
    },
    NotificationEvent.PASSWORD_CHANGED: {
        NotificationChannel.IN_APP,
        NotificationChannel.EMAIL,
    },
}


class NotificationDispatcher:
    """Persists in-app notifications and routes alerts to external channels."""

    def __init__(self, settings: Settings, redis: Redis) -> None:  # type: ignore[type-arg]
        self._settings = settings
        self._redis = redis
        self._email = EmailNotificationChannel(settings)
        self._telegram = TelegramChannel(settings)
        self._discord = DiscordChannel()
        self._slack = SlackChannel()
        self._push = PushChannel()
        self._sms = SmsChannel()

    async def dispatch(
        self,
        db: AsyncSession,
        *,
        user_id: UUID,
        event: NotificationEvent,
        payload: dict[str, Any],
        metadata: dict[str, Any] | None = None,
    ) -> Notification:
        """Create in-app notification and queue external channel delivery."""
        rendered = render_notification(self._settings, event, payload)
        notification_type = EVENT_TO_NOTIFICATION_TYPE[event]

        notification = Notification(
            user_id=user_id,
            type=notification_type,
            title=rendered.title,
            body=rendered.body,
            action_url=rendered.action_url,
            metadata_=metadata or payload,
        )
        db.add(notification)
        await db.flush()

        await self._publish_realtime(user_id, notification, event)
        if await self._is_muted(db, user_id):
            return notification

        channels = await self._resolve_channels(db, user_id, event)
        external = [c for c in channels if c != NotificationChannel.IN_APP]
        if external:
            digest_enabled = await self._digest_enabled(db, user_id)
            if digest_enabled:
                await self._queue_for_digest(
                    db,
                    user_id=user_id,
                    event=event,
                    rendered=rendered,
                    channels=external,
                )
            else:
                await self._enqueue_external_delivery(
                    user_id=user_id,
                    event=event.value,
                    rendered=rendered,
                    channels=[c.value for c in external],
                )

        logger.info(
            "notification_dispatched",
            user_id=str(user_id),
            event=event.value,
            channels=[c.value for c in channels],
        )
        return notification

    async def deliver_external(
        self,
        db: AsyncSession,
        *,
        user_id: UUID,
        event_value: str,
        rendered_dict: dict[str, Any],
        channel_values: list[str],
    ) -> list[dict[str, Any]]:
        """Deliver to external channels (called from Celery worker)."""
        logger.debug("notification_external_delivery", event=event_value, channels=channel_values)
        rendered = _rendered_from_dict(rendered_dict)
        user = await db.get(User, user_id)
        if user is None:
            return []

        channel_settings = await self._load_channel_settings(db, user_id)
        results: list[dict[str, Any]] = []

        for channel_value in channel_values:
            channel = NotificationChannel(channel_value)
            if channel == NotificationChannel.IN_APP:
                continue
            if not self._channel_configured(channel, channel_settings, user.email):
                continue

            config = channel_settings.get(channel, {})
            result = await self._send_channel(
                channel,
                user_email=user.email,
                config=config,
                rendered=rendered,
            )
            delivery = NotificationDelivery(
                user_id=user_id,
                event_type=event_value,
                channel=channel.value,
                status="sent" if result.success else "failed",
                attempts=1,
                last_error=result.error,
                payload={"title": rendered.title},
            )
            db.add(delivery)
            results.append(
                {
                    "channel": result.channel,
                    "success": result.success,
                    "error": result.error,
                },
            )
        return results

    async def notify_trade_copied(
        self,
        db: AsyncSession,
        *,
        user_id: UUID,
        symbol: str,
        action: str,
        follower_account_id: UUID,
        copy_group_id: UUID,
        latency_ms: int | None = None,
    ) -> Notification:
        return await self.dispatch(
            db,
            user_id=user_id,
            event=NotificationEvent.TRADE_COPIED,
            payload={
                "symbol": symbol,
                "action": action,
                "latency_ms": latency_ms,
            },
            metadata={
                "symbol": symbol,
                "action": action,
                "follower_account_id": str(follower_account_id),
                "copy_group_id": str(copy_group_id),
                "latency_ms": latency_ms,
            },
        )

    async def notify_trade_failed(
        self,
        db: AsyncSession,
        *,
        user_id: UUID,
        symbol: str,
        error: str,
        copy_group_id: UUID | None = None,
        follower_account_id: UUID | None = None,
    ) -> Notification:
        metadata: dict[str, Any] = {"symbol": symbol, "error": error}
        if copy_group_id:
            metadata["copy_group_id"] = str(copy_group_id)
        if follower_account_id:
            metadata["follower_account_id"] = str(follower_account_id)
        return await self.dispatch(
            db,
            user_id=user_id,
            event=NotificationEvent.TRADE_FAILED,
            payload={"symbol": symbol, "error": error},
            metadata=metadata,
        )

    async def notify_broker_offline(
        self,
        db: AsyncSession,
        *,
        user_id: UUID,
        broker: str,
        connection_name: str,
        connection_id: UUID,
    ) -> Notification:
        return await self.dispatch(
            db,
            user_id=user_id,
            event=NotificationEvent.BROKER_OFFLINE,
            payload={
                "broker": broker,
                "connection_name": connection_name,
            },
            metadata={
                "broker": broker,
                "connection_name": connection_name,
                "connection_id": str(connection_id),
            },
        )

    async def notify_risk_alert(
        self,
        db: AsyncSession,
        *,
        user_id: UUID,
        breach_type: str,
        message: str,
        account_id: UUID,
        breach_id: UUID | None = None,
        action_taken: str | None = None,
    ) -> Notification:
        metadata: dict[str, Any] = {
            "breach_type": breach_type,
            "message": message,
            "account_id": str(account_id),
        }
        if breach_id:
            metadata["breach_id"] = str(breach_id)
        if action_taken:
            metadata["action_taken"] = action_taken
        return await self.dispatch(
            db,
            user_id=user_id,
            event=NotificationEvent.RISK_ALERT,
            payload={
                "breach_type": breach_type,
                "message": message,
                "account_id": str(account_id),
            },
            metadata=metadata,
        )

    async def notify_subscription_expiry(
        self,
        db: AsyncSession,
        *,
        user_id: UUID,
        plan_name: str,
        days_remaining: int | None = None,
        subscription_id: UUID | None = None,
    ) -> Notification:
        metadata: dict[str, Any] = {"plan_name": plan_name, "days_remaining": days_remaining}
        if subscription_id:
            metadata["subscription_id"] = str(subscription_id)
        return await self.dispatch(
            db,
            user_id=user_id,
            event=NotificationEvent.SUBSCRIPTION_EXPIRY,
            payload={"plan_name": plan_name, "days_remaining": days_remaining},
            metadata=metadata,
        )

    async def notify_pnl_milestone(
        self,
        db: AsyncSession,
        *,
        user_id: UUID,
        milestone_label: str,
        pnl: float | None = None,
        account_id: UUID | None = None,
    ) -> Notification:
        metadata: dict[str, Any] = {"milestone_label": milestone_label, "pnl": pnl}
        if account_id:
            metadata["account_id"] = str(account_id)
        return await self.dispatch(
            db,
            user_id=user_id,
            event=NotificationEvent.PNL_MILESTONE,
            payload={"milestone_label": milestone_label, "pnl": pnl},
            metadata=metadata,
        )

    async def notify_large_profit(
        self,
        db: AsyncSession,
        *,
        user_id: UUID,
        symbol: str,
        pnl: float,
        account_id: UUID | None = None,
    ) -> Notification:
        metadata: dict[str, Any] = {"symbol": symbol, "pnl": pnl}
        if account_id:
            metadata["account_id"] = str(account_id)
        return await self.dispatch(
            db,
            user_id=user_id,
            event=NotificationEvent.LARGE_PROFIT,
            payload={"symbol": symbol, "pnl": pnl},
            metadata=metadata,
        )

    async def notify_large_loss(
        self,
        db: AsyncSession,
        *,
        user_id: UUID,
        symbol: str,
        pnl: float,
        account_id: UUID | None = None,
    ) -> Notification:
        metadata: dict[str, Any] = {"symbol": symbol, "pnl": pnl}
        if account_id:
            metadata["account_id"] = str(account_id)
        return await self.dispatch(
            db,
            user_id=user_id,
            event=NotificationEvent.LARGE_LOSS,
            payload={"symbol": symbol, "pnl": pnl},
            metadata=metadata,
        )

    async def notify_system_maintenance(
        self,
        db: AsyncSession,
        *,
        user_id: UUID,
        message: str,
        starts_at: str | None = None,
    ) -> Notification:
        return await self.dispatch(
            db,
            user_id=user_id,
            event=NotificationEvent.SYSTEM_MAINTENANCE,
            payload={"message": message, "starts_at": starts_at},
            metadata={"message": message, "starts_at": starts_at},
        )

    async def notify_user_invitation(
        self,
        db: AsyncSession,
        *,
        user_id: UUID,
        inviter_name: str,
        organization: str | None = None,
    ) -> Notification:
        return await self.dispatch(
            db,
            user_id=user_id,
            event=NotificationEvent.USER_INVITATION,
            payload={"inviter_name": inviter_name, "organization": organization},
            metadata={"inviter_name": inviter_name, "organization": organization},
        )

    async def notify_password_changed(
        self,
        db: AsyncSession,
        *,
        user_id: UUID,
    ) -> Notification:
        return await self.dispatch(
            db,
            user_id=user_id,
            event=NotificationEvent.PASSWORD_CHANGED,
            payload={},
            metadata={"changed_at": "now"},
        )

    async def _is_muted(self, db: AsyncSession, user_id: UUID) -> bool:
        from datetime import UTC, datetime

        settings = await db.get(NotificationUserSettings, user_id)
        if settings is None or settings.muted_until is None:
            return False
        return settings.muted_until > datetime.now(tz=UTC)

    async def _digest_enabled(self, db: AsyncSession, user_id: UUID) -> bool:
        settings = await db.get(NotificationUserSettings, user_id)
        return bool(settings and settings.digest_enabled)

    async def _queue_for_digest(
        self,
        db: AsyncSession,
        *,
        user_id: UUID,
        event: NotificationEvent,
        rendered: RenderedNotification,
        channels: list[NotificationChannel],
    ) -> None:
        for channel in channels:
            db.add(
                NotificationDigestItem(
                    user_id=user_id,
                    event_type=event,
                    channel=channel,
                    title=rendered.title,
                    body=rendered.body,
                    rendered=_rendered_to_dict(rendered),
                ),
            )
        await db.flush()

    async def _resolve_channels(
        self,
        db: AsyncSession,
        user_id: UUID,
        event: NotificationEvent,
    ) -> list[NotificationChannel]:
        prefs = await db.scalars(
            select(NotificationPreference).where(NotificationPreference.user_id == user_id),
        )
        pref_rows = prefs.all()
        if not pref_rows:
            return sorted(DEFAULT_EVENT_CHANNELS.get(event, {NotificationChannel.IN_APP}))

        enabled: list[NotificationChannel] = []
        for row in pref_rows:
            if row.event_type != event or not row.enabled:
                continue
            enabled.append(row.channel)
        if not enabled:
            return [NotificationChannel.IN_APP]
        if NotificationChannel.IN_APP not in enabled:
            enabled.append(NotificationChannel.IN_APP)
        return enabled

    async def _load_channel_settings(
        self,
        db: AsyncSession,
        user_id: UUID,
    ) -> dict[NotificationChannel, dict[str, object]]:
        rows = await db.scalars(
            select(NotificationChannelSetting).where(
                NotificationChannelSetting.user_id == user_id,
                NotificationChannelSetting.enabled.is_(True),
            ),
        )
        result: dict[NotificationChannel, dict[str, object]] = {}
        for row in rows.all():
            result[row.channel] = row.config or {}
        return result

    def _channel_configured(
        self,
        channel: NotificationChannel,
        settings: dict[NotificationChannel, dict[str, object]],
        user_email: str,
    ) -> bool:
        if channel == NotificationChannel.EMAIL:
            return bool(user_email)
        if channel == NotificationChannel.PUSH:
            return True
        config = settings.get(channel, {})
        if channel == NotificationChannel.TELEGRAM:
            return bool(
                config.get("chat_id")
                and (config.get("bot_token") or self._settings.telegram_bot_token),
            )
        if channel in {NotificationChannel.DISCORD, NotificationChannel.SLACK}:
            return bool(config.get("webhook_url"))
        if channel == NotificationChannel.SMS:
            return bool(config.get("phone_number"))
        return False

    async def _send_channel(
        self,
        channel: NotificationChannel,
        *,
        user_email: str,
        config: dict[str, object],
        rendered: RenderedNotification,
    ) -> Any:
        if channel == NotificationChannel.EMAIL:
            return await self._email.send(to_email=user_email, rendered=rendered)
        if channel == NotificationChannel.TELEGRAM:
            return await self._telegram.send(config=config, rendered=rendered)
        if channel == NotificationChannel.DISCORD:
            return await self._discord.send(config=config, rendered=rendered)
        if channel == NotificationChannel.SLACK:
            return await self._slack.send(config=config, rendered=rendered)
        if channel == NotificationChannel.PUSH:
            return await self._push.send(config=config, rendered=rendered)
        if channel == NotificationChannel.SMS:
            return await self._sms.send(config=config, rendered=rendered)
        msg = f"Unsupported channel: {channel}"
        raise ValueError(msg)

    async def _publish_realtime(
        self,
        user_id: UUID,
        notification: Notification,
        event: NotificationEvent,
    ) -> None:
        payload = {
            "type": "notification",
            "event": event.value,
            "notification_type": notification.type.value,
            "notification_id": str(notification.id),
            "title": notification.title,
            "body": notification.body,
            "action_url": notification.action_url,
        }
        await self._redis.publish(f"user:{user_id}:notifications", json.dumps(payload))

    async def _enqueue_external_delivery(
        self,
        *,
        user_id: UUID,
        event: str,
        rendered: RenderedNotification,
        channels: list[str],
    ) -> None:
        from tradeflow.workers.notification_tasks import deliver_notification_channels

        deliver_notification_channels.delay(
            str(user_id),
            event,
            _rendered_to_dict(rendered),
            channels,
        )


def _rendered_to_dict(rendered: RenderedNotification) -> dict[str, Any]:
    return {
        "title": rendered.title,
        "body": rendered.body,
        "action_url": rendered.action_url,
        "email_subject": rendered.email_subject,
        "email_body": rendered.email_body,
        "telegram_text": rendered.telegram_text,
        "discord_embed": rendered.discord_embed,
        "slack_text": rendered.slack_text,
        "slack_blocks": rendered.slack_blocks,
        "push_title": rendered.push_title,
        "push_body": rendered.push_body,
    }


def _rendered_from_dict(data: dict[str, Any]) -> RenderedNotification:
    return RenderedNotification(
        title=str(data["title"]),
        body=str(data["body"]),
        action_url=data.get("action_url"),
        email_subject=str(data["email_subject"]),
        email_body=str(data["email_body"]),
        telegram_text=str(data["telegram_text"]),
        discord_embed=dict(data["discord_embed"]),
        slack_text=str(data["slack_text"]),
        slack_blocks=list(data["slack_blocks"]),
        push_title=str(data["push_title"]),
        push_body=str(data["push_body"]),
    )
