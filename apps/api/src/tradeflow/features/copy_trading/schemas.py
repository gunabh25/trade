"""Copy trading API schemas."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, Field

from tradeflow.db.enums import (
    CopyEventAction,
    CopyEventResult,
    CopyFollowerStatus,
    CopyGroupMode,
    CopyGroupStatus,
    CopyMode,
    ExecutionLogStatus,
    OrderType,
)


class CreateCopyGroupRequest(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    leader_account_id: UUID
    mode: CopyGroupMode = CopyGroupMode.LIVE


class UpdateFollowerRequest(BaseModel):
    follower_account_id: UUID
    copy_mode: CopyMode
    sizing_value: Decimal = Field(gt=0)
    enabled: bool = True


class UpdateCopyGroupRequest(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    leader_account_id: UUID
    mode: CopyGroupMode = CopyGroupMode.LIVE
    followers: list[UpdateFollowerRequest] | None = None


class AddFollowerRequest(BaseModel):
    follower_account_id: UUID
    copy_mode: CopyMode
    sizing_value: Decimal = Field(gt=0)


class CopyGroupFollowerResponse(BaseModel):
    id: UUID
    follower_account_id: UUID
    enabled: bool
    copy_mode: CopyMode
    sizing_value: Decimal
    status: CopyFollowerStatus

    model_config = {"from_attributes": True}


class CopyGroupResponse(BaseModel):
    id: UUID
    name: str
    leader_account_id: UUID
    mode: CopyGroupMode
    status: CopyGroupStatus
    copying_enabled: bool
    sim_validated: bool
    followers: list[CopyGroupFollowerResponse] = Field(default_factory=list)
    created_at: datetime

    model_config = {"from_attributes": True}


class CopyEventResponse(BaseModel):
    id: UUID
    copy_group_id: UUID
    leader_account_id: UUID
    follower_account_id: UUID | None
    leader_event_id: str
    action: CopyEventAction
    result: CopyEventResult
    symbol: str | None
    quantity: int | None
    latency_ms: int | None
    error_message: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


class ExecutionLogResponse(BaseModel):
    id: UUID
    copy_group_id: UUID
    follower_account_id: UUID
    action: CopyEventAction
    status: ExecutionLogStatus
    attempt: int
    max_attempts: int
    error_message: str | None
    latency_ms: int | None
    created_at: datetime

    model_config = {"from_attributes": True}


class SimulateLeaderEventRequest(BaseModel):
    """Dev/test endpoint to inject a leader event into the copy engine."""

    symbol: str = Field(min_length=1, max_length=50)
    side: str = Field(pattern="^(buy|sell)$")
    order_type: OrderType = OrderType.MARKET
    quantity: int = Field(gt=0)
    price: Decimal | None = None
    stop_price: Decimal | None = None
    leader_order_id: str | None = None


class CopyEngineHealthResponse(BaseModel):
    active_groups: int
    retry_queue_depth: int
    dead_letter_count: int
