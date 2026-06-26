"""Per-user notification channel configuration and event preferences."""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, ForeignKey, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from tradeflow.db.base import Base
from tradeflow.db.enums import NotificationChannel, NotificationEvent
from tradeflow.db.mixins import TimestampMixin

if TYPE_CHECKING:
    from tradeflow.db.models.user import User


class NotificationChannelSetting(Base, TimestampMixin):
    """Channel credentials and enablement (Telegram, Discord, Slack, push, email)."""

    __tablename__ = "notification_channel_settings"
    __table_args__ = (UniqueConstraint("user_id", "channel", name="uq_notification_channel_user"),)

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    channel: Mapped[NotificationChannel] = mapped_column(String(20), nullable=False)
    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    config: Mapped[dict[str, object] | None] = mapped_column(JSONB, nullable=True)

    user: Mapped[User] = relationship(back_populates="notification_channels")


class NotificationPreference(Base, TimestampMixin):
    """Which events are delivered on which channels for a user."""

    __tablename__ = "notification_preferences"
    __table_args__ = (
        UniqueConstraint(
            "user_id",
            "event_type",
            "channel",
            name="uq_notification_preference_user_event_channel",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    event_type: Mapped[NotificationEvent] = mapped_column(String(50), nullable=False)
    channel: Mapped[NotificationChannel] = mapped_column(String(20), nullable=False)
    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    user: Mapped[User] = relationship(back_populates="notification_preferences")
