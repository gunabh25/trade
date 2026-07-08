"""Copy trading API routes."""

from __future__ import annotations

from uuid import UUID

from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends, Request

from tradeflow.core.container import Container
from tradeflow.core.dependencies.auth import CurrentUser, DbSession
from tradeflow.core.responses import SuccessResponse, success
from tradeflow.features.copy_trading.schemas import (
    AddFollowerRequest,
    CopyEngineHealthResponse,
    CopyEventResponse,
    CopyGroupFollowerResponse,
    CopyGroupResponse,
    CreateCopyGroupRequest,
    ExecutionLogResponse,
    SimulateLeaderEventRequest,
    UpdateCopyGroupRequest,
)
from tradeflow.features.copy_trading.service import CopyTradingService

router = APIRouter(prefix="/copy", tags=["Copy Trading"])


@router.post(
    "/groups",
    response_model=SuccessResponse[CopyGroupResponse],
    summary="Create a copy group",
)
@inject
async def create_copy_group(
    request: Request,
    payload: CreateCopyGroupRequest,
    db: DbSession,
    user: CurrentUser,
    copy_service: CopyTradingService = Depends(Provide[Container.copy_trading_service]),
) -> SuccessResponse[CopyGroupResponse]:
    result = await copy_service.create_group(db, user.id, payload)
    return success(result, request_id=getattr(request.state, "request_id", None))


@router.get(
    "/groups",
    response_model=SuccessResponse[list[CopyGroupResponse]],
    summary="List copy groups",
)
@inject
async def list_copy_groups(
    request: Request,
    db: DbSession,
    user: CurrentUser,
    copy_service: CopyTradingService = Depends(Provide[Container.copy_trading_service]),
) -> SuccessResponse[list[CopyGroupResponse]]:
    groups = await copy_service.list_groups(db, user.id)
    return success(groups, request_id=getattr(request.state, "request_id", None))


@router.get(
    "/groups/{group_id}",
    response_model=SuccessResponse[CopyGroupResponse],
    summary="Get copy group details",
)
@inject
async def get_copy_group(
    request: Request,
    group_id: UUID,
    db: DbSession,
    user: CurrentUser,
    copy_service: CopyTradingService = Depends(Provide[Container.copy_trading_service]),
) -> SuccessResponse[CopyGroupResponse]:
    group = await copy_service.get_group(db, user.id, group_id)
    return success(group, request_id=getattr(request.state, "request_id", None))


@router.put(
    "/groups/{group_id}",
    response_model=SuccessResponse[CopyGroupResponse],
    summary="Update a copy group",
)
@inject
async def update_copy_group(
    request: Request,
    group_id: UUID,
    payload: UpdateCopyGroupRequest,
    db: DbSession,
    user: CurrentUser,
    copy_service: CopyTradingService = Depends(Provide[Container.copy_trading_service]),
) -> SuccessResponse[CopyGroupResponse]:
    result = await copy_service.update_group(db, user.id, group_id, payload)
    return success(result, request_id=getattr(request.state, "request_id", None))


@router.post(
    "/groups/{group_id}/followers",
    response_model=SuccessResponse[CopyGroupFollowerResponse],
    summary="Add follower to copy group",
)
@inject
async def add_follower(
    request: Request,
    group_id: UUID,
    payload: AddFollowerRequest,
    db: DbSession,
    user: CurrentUser,
    copy_service: CopyTradingService = Depends(Provide[Container.copy_trading_service]),
) -> SuccessResponse[CopyGroupFollowerResponse]:
    result = await copy_service.add_follower(db, user.id, group_id, payload)
    return success(result, request_id=getattr(request.state, "request_id", None))


@router.post(
    "/groups/{group_id}/start",
    response_model=SuccessResponse[CopyGroupResponse],
    summary="Start copying",
)
@inject
async def start_copying(
    request: Request,
    group_id: UUID,
    db: DbSession,
    user: CurrentUser,
    copy_service: CopyTradingService = Depends(Provide[Container.copy_trading_service]),
) -> SuccessResponse[CopyGroupResponse]:
    result = await copy_service.start_copying(db, user.id, group_id)
    return success(result, request_id=getattr(request.state, "request_id", None))


@router.post(
    "/groups/{group_id}/stop",
    response_model=SuccessResponse[CopyGroupResponse],
    summary="Stop copying",
)
@inject
async def stop_copying(
    request: Request,
    group_id: UUID,
    db: DbSession,
    user: CurrentUser,
    copy_service: CopyTradingService = Depends(Provide[Container.copy_trading_service]),
) -> SuccessResponse[CopyGroupResponse]:
    result = await copy_service.stop_copying(db, user.id, group_id)
    return success(result, request_id=getattr(request.state, "request_id", None))


@router.delete(
    "/groups/{group_id}",
    response_model=SuccessResponse[dict[str, str]],
    summary="Delete a copy group",
)
@inject
async def delete_copy_group(
    request: Request,
    group_id: UUID,
    db: DbSession,
    user: CurrentUser,
    copy_service: CopyTradingService = Depends(Provide[Container.copy_trading_service]),
) -> SuccessResponse[dict[str, str]]:
    await copy_service.delete_group(db, user.id, group_id)
    return success({"status": "deleted"}, request_id=getattr(request.state, "request_id", None))


@router.get(
    "/groups/{group_id}/events",
    response_model=SuccessResponse[list[CopyEventResponse]],
    summary="List copy events (audit log)",
)
@inject
async def list_copy_events(
    request: Request,
    group_id: UUID,
    db: DbSession,
    user: CurrentUser,
    copy_service: CopyTradingService = Depends(Provide[Container.copy_trading_service]),
) -> SuccessResponse[list[CopyEventResponse]]:
    events = await copy_service.list_events(db, user.id, group_id)
    return success(events, request_id=getattr(request.state, "request_id", None))


@router.get(
    "/groups/{group_id}/execution-logs",
    response_model=SuccessResponse[list[ExecutionLogResponse]],
    summary="List execution logs with retry status",
)
@inject
async def list_execution_logs(
    request: Request,
    group_id: UUID,
    db: DbSession,
    user: CurrentUser,
    copy_service: CopyTradingService = Depends(Provide[Container.copy_trading_service]),
) -> SuccessResponse[list[ExecutionLogResponse]]:
    logs = await copy_service.list_execution_logs(db, user.id, group_id)
    return success(logs, request_id=getattr(request.state, "request_id", None))


@router.post(
    "/groups/{group_id}/simulate",
    response_model=SuccessResponse[list[dict[str, object]]],
    summary="Simulate a leader order event (dev/test)",
)
@inject
async def simulate_leader_event(
    request: Request,
    group_id: UUID,
    payload: SimulateLeaderEventRequest,
    db: DbSession,
    user: CurrentUser,
    copy_service: CopyTradingService = Depends(Provide[Container.copy_trading_service]),
) -> SuccessResponse[list[dict[str, object]]]:
    results = await copy_service.simulate_leader_event(db, user.id, group_id, payload)
    return success(results, request_id=getattr(request.state, "request_id", None))


@router.get(
    "/health",
    response_model=SuccessResponse[CopyEngineHealthResponse],
    summary="Copy engine health metrics",
)
@inject
async def copy_engine_health(
    request: Request,
    db: DbSession,
    user: CurrentUser,
    copy_service: CopyTradingService = Depends(Provide[Container.copy_trading_service]),
) -> SuccessResponse[CopyEngineHealthResponse]:
    health = await copy_service.engine_health(db, user.id)
    return success(health, request_id=getattr(request.state, "request_id", None))
