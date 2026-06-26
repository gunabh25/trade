"""Risk management API routes."""

from __future__ import annotations

from uuid import UUID

from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends, Request

from tradeflow.core.container import Container
from tradeflow.core.dependencies.auth import CurrentUser, DbSession
from tradeflow.core.responses import SuccessResponse, success
from tradeflow.db.enums import OrderSide
from tradeflow.features.risk.schemas import (
    CreateRiskRuleRequest,
    RiskBreachResponse,
    RiskMonitorStatusResponse,
    RiskRuleResponse,
    UpdateRiskRuleRequest,
)
from tradeflow.features.risk.service import RiskService
from tradeflow.risk.types import ProposedOrder

router = APIRouter(prefix="/risk", tags=["Risk Management"])


@router.post(
    "/rules",
    response_model=SuccessResponse[RiskRuleResponse],
    summary="Create risk rule for a trading account",
)
@inject
async def create_risk_rule(
    request: Request,
    payload: CreateRiskRuleRequest,
    db: DbSession,
    user: CurrentUser,
    risk_service: RiskService = Depends(Provide[Container.risk_service]),
) -> SuccessResponse[RiskRuleResponse]:
    result = await risk_service.create_rule(db, user.id, payload)
    return success(result, request_id=getattr(request.state, "request_id", None))


@router.get(
    "/rules",
    response_model=SuccessResponse[list[RiskRuleResponse]],
    summary="List all risk rules",
)
@inject
async def list_risk_rules(
    request: Request,
    db: DbSession,
    user: CurrentUser,
    risk_service: RiskService = Depends(Provide[Container.risk_service]),
) -> SuccessResponse[list[RiskRuleResponse]]:
    rules = await risk_service.list_rules(db, user.id)
    return success(rules, request_id=getattr(request.state, "request_id", None))


@router.get(
    "/rules/{rule_id}",
    response_model=SuccessResponse[RiskRuleResponse],
    summary="Get risk rule by ID",
)
@inject
async def get_risk_rule(
    request: Request,
    rule_id: UUID,
    db: DbSession,
    user: CurrentUser,
    risk_service: RiskService = Depends(Provide[Container.risk_service]),
) -> SuccessResponse[RiskRuleResponse]:
    rule = await risk_service.get_rule(db, user.id, rule_id)
    return success(rule, request_id=getattr(request.state, "request_id", None))


@router.put(
    "/rules/{rule_id}",
    response_model=SuccessResponse[RiskRuleResponse],
    summary="Update risk rule configuration",
)
@inject
async def update_risk_rule(
    request: Request,
    rule_id: UUID,
    payload: UpdateRiskRuleRequest,
    db: DbSession,
    user: CurrentUser,
    risk_service: RiskService = Depends(Provide[Container.risk_service]),
) -> SuccessResponse[RiskRuleResponse]:
    rule = await risk_service.update_rule(db, user.id, rule_id, payload)
    return success(rule, request_id=getattr(request.state, "request_id", None))


@router.delete(
    "/rules/{rule_id}",
    response_model=SuccessResponse[dict[str, str]],
    summary="Delete risk rule",
)
@inject
async def delete_risk_rule(
    request: Request,
    rule_id: UUID,
    db: DbSession,
    user: CurrentUser,
    risk_service: RiskService = Depends(Provide[Container.risk_service]),
) -> SuccessResponse[dict[str, str]]:
    await risk_service.delete_rule(db, user.id, rule_id)
    return success({"status": "deleted"}, request_id=getattr(request.state, "request_id", None))


@router.post(
    "/rules/{rule_id}/kill-switch/activate",
    response_model=SuccessResponse[RiskRuleResponse],
    summary="Activate kill switch",
)
@inject
async def activate_kill_switch(
    request: Request,
    rule_id: UUID,
    db: DbSession,
    user: CurrentUser,
    risk_service: RiskService = Depends(Provide[Container.risk_service]),
) -> SuccessResponse[RiskRuleResponse]:
    rule = await risk_service.activate_kill_switch(db, user.id, rule_id)
    return success(rule, request_id=getattr(request.state, "request_id", None))


@router.post(
    "/rules/{rule_id}/kill-switch/deactivate",
    response_model=SuccessResponse[RiskRuleResponse],
    summary="Deactivate kill switch",
)
@inject
async def deactivate_kill_switch(
    request: Request,
    rule_id: UUID,
    db: DbSession,
    user: CurrentUser,
    risk_service: RiskService = Depends(Provide[Container.risk_service]),
) -> SuccessResponse[RiskRuleResponse]:
    rule = await risk_service.deactivate_kill_switch(db, user.id, rule_id)
    return success(rule, request_id=getattr(request.state, "request_id", None))


@router.post(
    "/accounts/{account_id}/flatten",
    response_model=SuccessResponse[dict[str, int]],
    summary="Flatten all positions on an account",
)
@inject
async def flatten_account(
    request: Request,
    account_id: UUID,
    db: DbSession,
    user: CurrentUser,
    risk_service: RiskService = Depends(Provide[Container.risk_service]),
) -> SuccessResponse[dict[str, int]]:
    result = await risk_service.flatten_account(db, user.id, account_id)
    return success(result, request_id=getattr(request.state, "request_id", None))


@router.get(
    "/accounts/{account_id}/status",
    response_model=SuccessResponse[RiskMonitorStatusResponse],
    summary="Real-time risk monitor status",
)
@inject
async def get_monitor_status(
    request: Request,
    account_id: UUID,
    db: DbSession,
    user: CurrentUser,
    risk_service: RiskService = Depends(Provide[Container.risk_service]),
) -> SuccessResponse[RiskMonitorStatusResponse]:
    status = await risk_service.get_monitor_status(db, user.id, account_id)
    return success(status, request_id=getattr(request.state, "request_id", None))


@router.get(
    "/breaches",
    response_model=SuccessResponse[list[RiskBreachResponse]],
    summary="List risk breach history",
)
@inject
async def list_breaches(
    request: Request,
    db: DbSession,
    user: CurrentUser,
    account_id: UUID | None = None,
    risk_service: RiskService = Depends(Provide[Container.risk_service]),
) -> SuccessResponse[list[RiskBreachResponse]]:
    breaches = await risk_service.list_breaches(db, user.id, account_id=account_id)
    return success(breaches, request_id=getattr(request.state, "request_id", None))


@router.post(
    "/accounts/{account_id}/check",
    response_model=SuccessResponse[dict[str, object]],
    summary="Pre-trade risk check",
)
@inject
async def check_pre_trade(
    request: Request,
    account_id: UUID,
    symbol: str,
    side: str,
    quantity: int,
    db: DbSession,
    user: CurrentUser,
    risk_service: RiskService = Depends(Provide[Container.risk_service]),
) -> SuccessResponse[dict[str, object]]:
    order = ProposedOrder(symbol=symbol, side=OrderSide(side), quantity=quantity)
    result = await risk_service.check_pre_trade(db, user.id, account_id, order)
    return success(result, request_id=getattr(request.state, "request_id", None))
