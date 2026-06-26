"""Notification platform — user settings, delivery log, digest queue."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from tradeflow.db.base import Base
from tradeflow.db.enums import NotificationChannel, NotificationEvent
from tradeflow.db.mixins import TimestampMixin

if TYPE_CHECKING:
    from tradeflow.db.models.user import User


class NotificationUserSettings(Base, TimestampMixin):
    """Global notification preferences: mute and digest."""

    __tablename__ = "notification_user_settings"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        primary_key=True,
    )
    muted_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    digest_enabled: Mapped[bool] = mapped_column(nullable=False, default=False)
    digest_frequency: Mapped[str] = mapped_column(String(20), nullable=False, default="daily")
    digest_hour_utc: Mapped[int] = mapped_column(Integer, nullable=False, default=8)

    user: Mapped[User] = relationship(back_populates="notification_user_settings")


class NotificationDelivery(Base, TimestampMixin):
    """Delivery attempt log for retry and observability."""

    __tablename__ = "notification_deliveries"

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
    event_type: Mapped[str] = mapped_column(String(50), nullable=False)
    channel: Mapped[str] = mapped_column(String(20), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="pending")
    attempts: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    last_error: Mapped[str | None] = mapped_column(Text, nullable=True)
    payload: Mapped[dict[str, object] | None] = mapped_column(JSONB, nullable=True)

    user: Mapped[User] = relationship()


class NotificationDigestItem(Base, TimestampMixin):
    """Queued notification for batched digest delivery."""

    __tablename__ = "notification_digest_queue"

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
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    rendered: Mapped[dict[str, object]] = mapped_column(JSONB, nullable=False)
    delivered_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    user: Mapped[User] = relationship(back_populates="notification_digest_items")
