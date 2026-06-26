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
