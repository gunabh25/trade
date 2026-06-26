"""Notification inbox and preference management."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from tradeflow.db.enums import NotificationChannel, NotificationEvent
from tradeflow.db.models.notification import Notification
from tradeflow.db.models.notification_settings import (
    NotificationChannelSetting,
    NotificationPreference,
)
from tradeflow.features.notifications.schemas import (
    ChannelSettingResponse,
    NotificationPreferencesResponse,
    NotificationResponse,
    PreferenceResponse,
)
from tradeflow.notifications.dispatcher import DEFAULT_EVENT_CHANNELS
from tradeflow.notifications.events import ALL_NOTIFICATION_EVENTS


class NotificationService:
    """CRUD for in-app notifications and user channel preferences."""

    async def list_notifications(
        self,
        db: AsyncSession,
        user_id: UUID,
        *,
        unread_only: bool = False,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[NotificationResponse], int]:
        query = select(Notification).where(
            Notification.user_id == user_id,
            Notification.deleted_at.is_(None),
        )
        if unread_only:
            query = query.where(Notification.read_at.is_(None))

        count_query = select(func.count()).select_from(query.subquery())
        total = int(await db.scalar(count_query) or 0)

        rows = await db.scalars(
            query.order_by(Notification.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size),
        )
        items = [_to_notification_response(row) for row in rows.all()]
        return items, total

    async def mark_read(
        self,
        db: AsyncSession,
        user_id: UUID,
        notification_id: UUID,
    ) -> NotificationResponse | None:
        notification = await db.scalar(
            select(Notification).where(
                Notification.id == notification_id,
                Notification.user_id == user_id,
                Notification.deleted_at.is_(None),
            ),
        )
        if notification is None:
            return None
        if notification.read_at is None:
            notification.read_at = datetime.now(tz=UTC)
            await db.flush()
        return _to_notification_response(notification)

    async def mark_all_read(self, db: AsyncSession, user_id: UUID) -> int:
        result = await db.execute(
            update(Notification)
            .where(
                Notification.user_id == user_id,
                Notification.read_at.is_(None),
                Notification.deleted_at.is_(None),
            )
            .values(read_at=datetime.now(tz=UTC)),
        )
        await db.flush()
        return int(result.rowcount or 0)

    async def get_preferences(
        self,
        db: AsyncSession,
        user_id: UUID,
    ) -> NotificationPreferencesResponse:
        channel_rows = await db.scalars(
            select(NotificationChannelSetting).where(
                NotificationChannelSetting.user_id == user_id,
            ),
        )
        pref_rows = await db.scalars(
            select(NotificationPreference).where(NotificationPreference.user_id == user_id),
        )

        channels = [
            ChannelSettingResponse(
                channel=row.channel,
                enabled=row.enabled,
                config=row.config,
            )
            for row in channel_rows.all()
        ]
        preferences = [
            PreferenceResponse(
                event_type=row.event_type,
                channel=row.channel,
                enabled=row.enabled,
            )
            for row in pref_rows.all()
        ]

        if not preferences:
            preferences = self._default_preferences()

        return NotificationPreferencesResponse(
            channels=channels,
            preferences=preferences,
            available_events=ALL_NOTIFICATION_EVENTS,
            available_channels=list(NotificationChannel),
        )

    async def upsert_channel_setting(
        self,
        db: AsyncSession,
        user_id: UUID,
        channel: NotificationChannel,
        *,
        enabled: bool,
        config: dict[str, object] | None,
    ) -> ChannelSettingResponse:
        row = await db.scalar(
            select(NotificationChannelSetting).where(
                NotificationChannelSetting.user_id == user_id,
                NotificationChannelSetting.channel == channel,
            ),
        )
        if row is None:
            row = NotificationChannelSetting(
                user_id=user_id,
                channel=channel,
                enabled=enabled,
                config=config,
            )
            db.add(row)
        else:
            row.enabled = enabled
            row.config = config
        await db.flush()
        return ChannelSettingResponse(channel=row.channel, enabled=row.enabled, config=row.config)

    async def upsert_preference(
        self,
        db: AsyncSession,
        user_id: UUID,
        event_type: NotificationEvent,
        channel: NotificationChannel,
        *,
        enabled: bool,
    ) -> PreferenceResponse:
        row = await db.scalar(
            select(NotificationPreference).where(
                NotificationPreference.user_id == user_id,
                NotificationPreference.event_type == event_type,
                NotificationPreference.channel == channel,
            ),
        )
        if row is None:
            row = NotificationPreference(
                user_id=user_id,
                event_type=event_type,
                channel=channel,
                enabled=enabled,
            )
            db.add(row)
        else:
            row.enabled = enabled
        await db.flush()
        return PreferenceResponse(
            event_type=row.event_type,
            channel=row.channel,
            enabled=row.enabled,
        )

    def _default_preferences(self) -> list[PreferenceResponse]:
        prefs: list[PreferenceResponse] = []
        for event, channels in DEFAULT_EVENT_CHANNELS.items():
            for channel in channels:
                prefs.append(
                    PreferenceResponse(
                        event_type=event,
                        channel=channel,
                        enabled=True,
                    ),
                )
        return prefs


def _to_notification_response(row: Notification) -> NotificationResponse:
    return NotificationResponse(
        id=row.id,
        type=row.type,
        title=row.title,
        body=row.body,
        read=row.read_at is not None,
        action_url=row.action_url,
        metadata=row.metadata_,
        created_at=row.created_at,
    )
