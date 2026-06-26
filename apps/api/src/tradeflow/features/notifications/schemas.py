"""Notification API schemas."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from tradeflow.db.enums import NotificationChannel, NotificationEvent, NotificationType


class NotificationResponse(BaseModel):
    id: UUID
    type: NotificationType
    title: str
    body: str
    read: bool
    action_url: str | None
    metadata: dict[str, object] | None = Field(default=None, validation_alias="metadata_")
    created_at: datetime

    model_config = {"from_attributes": True}


class ChannelSettingResponse(BaseModel):
    channel: NotificationChannel
    enabled: bool
    config: dict[str, object] | None = None


class UpdateChannelSettingRequest(BaseModel):
    enabled: bool = True
    config: dict[str, object] | None = None


class PreferenceResponse(BaseModel):
    event_type: NotificationEvent
    channel: NotificationChannel
    enabled: bool


class UpdatePreferenceRequest(BaseModel):
    event_type: NotificationEvent
    channel: NotificationChannel
    enabled: bool


class NotificationPreferencesResponse(BaseModel):
    channels: list[ChannelSettingResponse]
    preferences: list[PreferenceResponse]
    available_events: list[NotificationEvent]
    available_channels: list[NotificationChannel]
    event_labels: dict[str, str] = Field(default_factory=dict)


class NotificationUserSettingsResponse(BaseModel):
    muted_until: datetime | None = None
    digest_enabled: bool = False
    digest_frequency: str = "daily"
    digest_hour_utc: int = 8


class UpdateNotificationUserSettingsRequest(BaseModel):
    muted_until: datetime | None = None
    mute_hours: int | None = Field(default=None, ge=1, le=168)
    clear_mute: bool = False
    digest_enabled: bool | None = None
    digest_frequency: str | None = Field(default=None, pattern="^(daily|weekly)$")
    digest_hour_utc: int | None = Field(default=None, ge=0, le=23)


class BulkUpdatePreferencesRequest(BaseModel):
    preferences: list[UpdatePreferenceRequest]


class UnreadCountResponse(BaseModel):
    count: int
