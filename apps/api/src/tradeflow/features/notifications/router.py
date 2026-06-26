"""Notification inbox and preferences API."""

from __future__ import annotations

from uuid import UUID

from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends, HTTPException, Query, Request, status

from tradeflow.core.container import Container
from tradeflow.core.dependencies.auth import CurrentUser, DbSession
from tradeflow.core.responses import SuccessResponse, success
from tradeflow.db.enums import NotificationChannel
from tradeflow.features.notifications.schemas import (
    BulkUpdatePreferencesRequest,
    NotificationPreferencesResponse,
    NotificationResponse,
    NotificationUserSettingsResponse,
    UnreadCountResponse,
    UpdateChannelSettingRequest,
    UpdateNotificationUserSettingsRequest,
    UpdatePreferenceRequest,
)
from tradeflow.features.notifications.service import NotificationService

router = APIRouter(prefix="/notifications", tags=["Notifications"])


@router.get(
    "",
    response_model=SuccessResponse[dict[str, object]],
    summary="List in-app notifications",
)
@inject
async def list_notifications(
    request: Request,
    db: DbSession,
    user: CurrentUser,
    unread_only: bool = False,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    notification_service: NotificationService = Depends(Provide[Container.notification_service]),
) -> SuccessResponse[dict[str, object]]:
    items, total = await notification_service.list_notifications(
        db,
        user.id,
        unread_only=unread_only,
        page=page,
        page_size=page_size,
    )
    total_pages = max(1, (total + page_size - 1) // page_size)
    return success(
        {
            "items": items,
            "meta": {
                "page": page,
                "pageSize": page_size,
                "total": total,
                "totalPages": total_pages,
            },
        },
        request_id=request.state.request_id,
    )


@router.post(
    "/{notification_id}/read",
    response_model=SuccessResponse[NotificationResponse],
    summary="Mark a notification as read",
)
@inject
async def mark_notification_read(
    notification_id: UUID,
    request: Request,
    db: DbSession,
    user: CurrentUser,
    notification_service: NotificationService = Depends(Provide[Container.notification_service]),
) -> SuccessResponse[NotificationResponse]:
    item = await notification_service.mark_read(db, user.id, notification_id)
    if item is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Notification not found")
    return success(item, request_id=request.state.request_id)


@router.post(
    "/read-all",
    response_model=SuccessResponse[dict[str, int]],
    summary="Mark all notifications as read",
)
@inject
async def mark_all_notifications_read(
    request: Request,
    db: DbSession,
    user: CurrentUser,
    notification_service: NotificationService = Depends(Provide[Container.notification_service]),
) -> SuccessResponse[dict[str, int]]:
    count = await notification_service.mark_all_read(db, user.id)
    return success({"updated": count}, request_id=request.state.request_id)


@router.get(
    "/unread-count",
    response_model=SuccessResponse[UnreadCountResponse],
    summary="Get unread notification count",
)
@inject
async def get_unread_count(
    request: Request,
    db: DbSession,
    user: CurrentUser,
    notification_service: NotificationService = Depends(Provide[Container.notification_service]),
) -> SuccessResponse[UnreadCountResponse]:
    count = await notification_service.unread_count(db, user.id)
    return success(UnreadCountResponse(count=count), request_id=request.state.request_id)


@router.get(
    "/settings",
    response_model=SuccessResponse[NotificationUserSettingsResponse],
    summary="Get mute and digest settings",
)
@inject
async def get_notification_settings(
    request: Request,
    db: DbSession,
    user: CurrentUser,
    notification_service: NotificationService = Depends(Provide[Container.notification_service]),
) -> SuccessResponse[NotificationUserSettingsResponse]:
    settings = await notification_service.get_user_settings(db, user.id)
    return success(settings, request_id=request.state.request_id)


@router.put(
    "/settings",
    response_model=SuccessResponse[NotificationUserSettingsResponse],
    summary="Update mute and digest settings",
)
@inject
async def update_notification_settings(
    body: UpdateNotificationUserSettingsRequest,
    request: Request,
    db: DbSession,
    user: CurrentUser,
    notification_service: NotificationService = Depends(Provide[Container.notification_service]),
) -> SuccessResponse[NotificationUserSettingsResponse]:
    settings = await notification_service.update_user_settings(db, user.id, body)
    return success(settings, request_id=request.state.request_id)


@router.get(
    "/preferences",
    response_model=SuccessResponse[NotificationPreferencesResponse],
    summary="Get notification channel settings and event preferences",
)
@inject
async def get_notification_preferences(
    request: Request,
    db: DbSession,
    user: CurrentUser,
    notification_service: NotificationService = Depends(Provide[Container.notification_service]),
) -> SuccessResponse[NotificationPreferencesResponse]:
    prefs = await notification_service.get_preferences(db, user.id)
    return success(prefs, request_id=request.state.request_id)


@router.put(
    "/channels/{channel}",
    response_model=SuccessResponse[dict[str, object]],
    summary="Update notification channel configuration",
)
@inject
async def update_channel_setting(
    channel: NotificationChannel,
    body: UpdateChannelSettingRequest,
    request: Request,
    db: DbSession,
    user: CurrentUser,
    notification_service: NotificationService = Depends(Provide[Container.notification_service]),
) -> SuccessResponse[dict[str, object]]:
    item = await notification_service.upsert_channel_setting(
        db,
        user.id,
        channel,
        enabled=body.enabled,
        config=body.config,
    )
    return success(item.model_dump(), request_id=request.state.request_id)


@router.put(
    "/preferences",
    response_model=SuccessResponse[dict[str, object]],
    summary="Update event/channel notification preference",
)
@inject
async def update_notification_preference(
    body: UpdatePreferenceRequest,
    request: Request,
    db: DbSession,
    user: CurrentUser,
    notification_service: NotificationService = Depends(Provide[Container.notification_service]),
) -> SuccessResponse[dict[str, object]]:
    item = await notification_service.upsert_preference(
        db,
        user.id,
        body.event_type,
        body.channel,
        enabled=body.enabled,
    )
    return success(item.model_dump(), request_id=request.state.request_id)


@router.put(
    "/preferences/bulk",
    response_model=SuccessResponse[dict[str, object]],
    summary="Bulk update event/channel notification preferences",
)
@inject
async def bulk_update_notification_preferences(
    body: BulkUpdatePreferencesRequest,
    request: Request,
    db: DbSession,
    user: CurrentUser,
    notification_service: NotificationService = Depends(Provide[Container.notification_service]),
) -> SuccessResponse[dict[str, object]]:
    items = await notification_service.bulk_update_preferences(
        db,
        user.id,
        [(pref.event_type, pref.channel, pref.enabled) for pref in body.preferences],
    )
    return success(
        {"updated": len(items), "preferences": [item.model_dump() for item in items]},
        request_id=request.state.request_id,
    )
