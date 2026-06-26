"""Admin portal API schemas."""

from __future__ import annotations

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field

from tradeflow.db.enums import (
    AnnouncementStatus,
    AuditAction,
    ConnectionStatus,
    RoleName,
    SubscriptionStatus,
    SupportTicketPriority,
    SupportTicketStatus,
    SystemLogLevel,
)


class AdminOverviewResponse(BaseModel):
    total_users: int
    active_users: int
    total_subscriptions: int
    active_subscriptions: int
    open_tickets: int
    broker_connections: int
    broker_errors: int
    published_announcements: int
    enabled_feature_flags: int
    total_organizations: int = 0
    total_trading_accounts: int = 0


class AdminUserResponse(BaseModel):
    id: UUID
    email: str
    first_name: str | None
    last_name: str | None
    is_active: bool
    roles: list[str]
    created_at: datetime
    email_verified: bool


class AdminUpdateUserRequest(BaseModel):
    is_active: bool | None = None
    first_name: str | None = None
    last_name: str | None = None


class AdminRoleAssignmentRequest(BaseModel):
    role: RoleName


class AdminPermissionsResponse(BaseModel):
    roles: list[str]
    permissions: dict[str, list[str]]


class AdminAuditLogResponse(BaseModel):
    id: UUID
    user_id: UUID | None
    user_email: str | None
    action: AuditAction
    resource_type: str
    resource_id: UUID | None
    ip_address: str | None
    created_at: datetime
    metadata: dict[str, object] | None = Field(default=None, validation_alias="metadata_")


class AdminSupportTicketResponse(BaseModel):
    id: UUID
    user_id: UUID
    user_email: str
    assigned_to_id: UUID | None
    subject: str
    description: str
    status: SupportTicketStatus
    priority: SupportTicketPriority
    created_at: datetime
    updated_at: datetime
    resolved_at: datetime | None


class CreateSupportTicketRequest(BaseModel):
    user_id: UUID
    subject: str = Field(min_length=3, max_length=200)
    description: str = Field(min_length=5)
    priority: SupportTicketPriority = SupportTicketPriority.MEDIUM


class UpdateSupportTicketRequest(BaseModel):
    status: SupportTicketStatus | None = None
    priority: SupportTicketPriority | None = None
    assigned_to_id: UUID | None = None


class AdminBrokerStatusResponse(BaseModel):
    id: UUID
    user_id: UUID
    user_email: str
    broker: str
    name: str
    status: ConnectionStatus
    last_connected_at: datetime | None
    last_error: str | None
    live_connected: bool | None = None
    live_latency_ms: float | None = None


class FeatureFlagResponse(BaseModel):
    id: UUID
    key: str
    name: str
    description: str | None
    enabled: bool
    rules: dict[str, object] | None
    updated_at: datetime

    model_config = {"from_attributes": True}


class CreateFeatureFlagRequest(BaseModel):
    key: str = Field(min_length=2, max_length=100)
    name: str
    description: str | None = None
    enabled: bool = False
    rules: dict[str, object] | None = None


class UpdateFeatureFlagRequest(BaseModel):
    name: str | None = None
    description: str | None = None
    enabled: bool | None = None
    rules: dict[str, object] | None = None


class AnnouncementResponse(BaseModel):
    id: UUID
    title: str
    body: str
    status: AnnouncementStatus
    starts_at: datetime | None
    ends_at: datetime | None
    target_roles: list[str] | None
    created_at: datetime

    model_config = {"from_attributes": True}


class CreateAnnouncementRequest(BaseModel):
    title: str = Field(min_length=3, max_length=200)
    body: str = Field(min_length=5)
    status: AnnouncementStatus = AnnouncementStatus.DRAFT
    starts_at: datetime | None = None
    ends_at: datetime | None = None
    target_roles: list[str] | None = None


class UpdateAnnouncementRequest(BaseModel):
    title: str | None = None
    body: str | None = None
    status: AnnouncementStatus | None = None
    starts_at: datetime | None = None
    ends_at: datetime | None = None
    target_roles: list[str] | None = None


class AdminAnalyticsResponse(BaseModel):
    users_by_month: list[dict[str, object]]
    subscriptions_by_plan: list[dict[str, object]]
    tickets_by_status: list[dict[str, object]]
    connections_by_broker: list[dict[str, object]]
    mrr_cents: int


class AdminHealthResponse(BaseModel):
    status: str
    environment: str
    version: str
    database: dict[str, object]
    redis: dict[str, object]
    broker_monitor: dict[str, object]
    celery: dict[str, object]


class SystemLogResponse(BaseModel):
    id: UUID
    level: SystemLogLevel
    source: str
    message: str
    user_id: UUID | None
    metadata: dict[str, object] | None = Field(default=None, validation_alias="metadata_")
    created_at: datetime

    model_config = {"from_attributes": True}


class AdminSearchResult(BaseModel):
    type: str
    id: str
    title: str
    subtitle: str | None = None


class AdminSearchResponse(BaseModel):
    query: str
    results: list[AdminSearchResult]


class AdminSubscriptionSummary(BaseModel):
    id: UUID
    user_id: UUID
    user_email: str
    status: SubscriptionStatus
    plan_code: str
    plan_name: str
    trial_ends_at: datetime | None
    current_period_end: datetime | None


class AdminOrganizationResponse(BaseModel):
    id: UUID
    name: str
    slug: str
    plan_code: str
    is_active: bool
    owner_user_id: UUID | None
    owner_email: str | None
    member_count: int
    created_at: datetime


class CreateOrganizationRequest(BaseModel):
    name: str = Field(min_length=2, max_length=200)
    slug: str = Field(min_length=2, max_length=100, pattern=r"^[a-z0-9-]+$")
    plan_code: str = "free"
    owner_user_id: UUID | None = None


class UpdateOrganizationRequest(BaseModel):
    name: str | None = None
    plan_code: str | None = None
    is_active: bool | None = None
    owner_user_id: UUID | None = None


class AdminTradingAccountResponse(BaseModel):
    id: UUID
    user_id: UUID
    user_email: str
    broker_connection_id: UUID
    name: str
    external_account_id: str
    account_type: str
    account_role: str
    status: str
    currency: str
    balance: float | None
    created_at: datetime


class AdminNotificationDeliveryResponse(BaseModel):
    id: UUID
    user_id: UUID
    user_email: str | None
    event_type: str
    channel: str
    status: str
    attempts: int
    last_error: str | None
    created_at: datetime


class BulkUserActionRequest(BaseModel):
    user_ids: list[UUID] = Field(min_length=1, max_length=100)
    action: Literal["activate", "deactivate"]


class BulkUserActionResponse(BaseModel):
    updated: int
    user_ids: list[UUID]
