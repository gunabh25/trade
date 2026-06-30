"""Broker integration API routes."""

from __future__ import annotations

import json
from uuid import UUID

from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends, Header, Request

from tradeflow.core.container import Container
from tradeflow.core.dependencies.auth import CurrentUser, DbSession
from tradeflow.core.responses import SuccessResponse, success
from tradeflow.features.broker.schemas import (
    BrokerAccountResponse,
    BrokerConnectionResponse,
    BrokerHealthResponse,
    BrokerOrderResponse,
    BrokerPositionResponse,
    CreateBrokerConnectionRequest,
    FlattenPositionRequest,
    ModifyOrderRequest,
    PlaceOrderRequest,
    SupportedBrokersResponse,
)
from tradeflow.features.broker.service import BrokerConnectionService

router = APIRouter(prefix="/broker", tags=["Broker Integrations"])


@router.get(
    "/supported",
    response_model=SuccessResponse[SupportedBrokersResponse],
    summary="List supported broker types",
)
@inject
async def list_supported_brokers(
    request: Request,
    broker_service: BrokerConnectionService = Depends(Provide[Container.broker_service]),
) -> SuccessResponse[SupportedBrokersResponse]:
    result = broker_service.list_supported_brokers()
    return success(result, request_id=getattr(request.state, "request_id", None))


@router.get(
    "/connections",
    response_model=SuccessResponse[list[BrokerConnectionResponse]],
    summary="List broker connections",
)
@inject
async def list_connections(
    request: Request,
    db: DbSession,
    user: CurrentUser,
    broker_service: BrokerConnectionService = Depends(Provide[Container.broker_service]),
) -> SuccessResponse[list[BrokerConnectionResponse]]:
    connections = await broker_service.list_connections(db, user.id)
    return success(connections, request_id=getattr(request.state, "request_id", None))


@router.post(
    "/connections",
    response_model=SuccessResponse[BrokerConnectionResponse],
    summary="Create a broker connection",
)
@inject
async def create_connection(
    request: Request,
    payload: CreateBrokerConnectionRequest,
    db: DbSession,
    user: CurrentUser,
    broker_service: BrokerConnectionService = Depends(Provide[Container.broker_service]),
) -> SuccessResponse[BrokerConnectionResponse]:
    connection = await broker_service.create_connection(db, user.id, payload)
    return success(connection, request_id=getattr(request.state, "request_id", None))


@router.post(
    "/connections/{connection_id}/connect",
    response_model=SuccessResponse[BrokerHealthResponse],
    summary="Connect to broker",
)
@inject
async def connect_broker(
    request: Request,
    connection_id: UUID,
    db: DbSession,
    user: CurrentUser,
    broker_service: BrokerConnectionService = Depends(Provide[Container.broker_service]),
) -> SuccessResponse[BrokerHealthResponse]:
    health = await broker_service.connect(db, user.id, connection_id)
    return success(health, request_id=getattr(request.state, "request_id", None))


@router.post(
    "/connections/{connection_id}/disconnect",
    response_model=SuccessResponse[BrokerConnectionResponse],
    summary="Disconnect from broker",
)
@inject
async def disconnect_broker(
    request: Request,
    connection_id: UUID,
    db: DbSession,
    user: CurrentUser,
    broker_service: BrokerConnectionService = Depends(Provide[Container.broker_service]),
) -> SuccessResponse[BrokerConnectionResponse]:
    connection = await broker_service.disconnect(db, user.id, connection_id)
    return success(connection, request_id=getattr(request.state, "request_id", None))


@router.get(
    "/connections/{connection_id}/health",
    response_model=SuccessResponse[BrokerHealthResponse],
    summary="Broker connection health",
)
@inject
async def connection_health(
    request: Request,
    connection_id: UUID,
    db: DbSession,
    user: CurrentUser,
    broker_service: BrokerConnectionService = Depends(Provide[Container.broker_service]),
) -> SuccessResponse[BrokerHealthResponse]:
    health = await broker_service.get_health(db, user.id, connection_id)
    return success(health, request_id=getattr(request.state, "request_id", None))


@router.get(
    "/connections/{connection_id}/accounts",
    response_model=SuccessResponse[list[BrokerAccountResponse]],
    summary="Fetch broker accounts",
)
@inject
async def fetch_accounts(
    request: Request,
    connection_id: UUID,
    db: DbSession,
    user: CurrentUser,
    broker_service: BrokerConnectionService = Depends(Provide[Container.broker_service]),
) -> SuccessResponse[list[BrokerAccountResponse]]:
    accounts = await broker_service.fetch_accounts(db, user.id, connection_id)
    return success(accounts, request_id=getattr(request.state, "request_id", None))


@router.get(
    "/connections/{connection_id}/accounts/{account_id}/orders",
    response_model=SuccessResponse[list[BrokerOrderResponse]],
    summary="Fetch open orders",
)
@inject
async def fetch_orders(
    request: Request,
    connection_id: UUID,
    account_id: str,
    db: DbSession,
    user: CurrentUser,
    broker_service: BrokerConnectionService = Depends(Provide[Container.broker_service]),
) -> SuccessResponse[list[BrokerOrderResponse]]:
    orders = await broker_service.fetch_orders(db, user.id, connection_id, account_id)
    return success(orders, request_id=getattr(request.state, "request_id", None))


@router.get(
    "/connections/{connection_id}/accounts/{account_id}/positions",
    response_model=SuccessResponse[list[BrokerPositionResponse]],
    summary="Fetch open positions",
)
@inject
async def fetch_positions(
    request: Request,
    connection_id: UUID,
    account_id: str,
    db: DbSession,
    user: CurrentUser,
    broker_service: BrokerConnectionService = Depends(Provide[Container.broker_service]),
) -> SuccessResponse[list[BrokerPositionResponse]]:
    positions = await broker_service.fetch_positions(db, user.id, connection_id, account_id)
    return success(positions, request_id=getattr(request.state, "request_id", None))


@router.post(
    "/connections/{connection_id}/orders",
    response_model=SuccessResponse[BrokerOrderResponse],
    summary="Place an order",
)
@inject
async def place_order(
    request: Request,
    connection_id: UUID,
    payload: PlaceOrderRequest,
    db: DbSession,
    user: CurrentUser,
    broker_service: BrokerConnectionService = Depends(Provide[Container.broker_service]),
) -> SuccessResponse[BrokerOrderResponse]:
    order = await broker_service.place_order(db, user.id, connection_id, payload)
    return success(order, request_id=getattr(request.state, "request_id", None))


@router.patch(
    "/connections/{connection_id}/orders/{order_id}",
    response_model=SuccessResponse[BrokerOrderResponse],
    summary="Modify an open order",
)
@inject
async def modify_order(
    request: Request,
    connection_id: UUID,
    order_id: str,
    payload: ModifyOrderRequest,
    db: DbSession,
    user: CurrentUser,
    broker_service: BrokerConnectionService = Depends(Provide[Container.broker_service]),
) -> SuccessResponse[BrokerOrderResponse]:
    order = await broker_service.modify_order(db, user.id, connection_id, order_id, payload)
    return success(order, request_id=getattr(request.state, "request_id", None))


@router.delete(
    "/connections/{connection_id}/orders/{order_id}",
    response_model=SuccessResponse[BrokerOrderResponse],
    summary="Cancel an open order",
)
@inject
async def cancel_order(
    request: Request,
    connection_id: UUID,
    order_id: str,
    db: DbSession,
    user: CurrentUser,
    broker_service: BrokerConnectionService = Depends(Provide[Container.broker_service]),
) -> SuccessResponse[BrokerOrderResponse]:
    order = await broker_service.cancel_order(db, user.id, connection_id, order_id)
    return success(order, request_id=getattr(request.state, "request_id", None))


@router.post(
    "/connections/{connection_id}/flatten",
    response_model=SuccessResponse[BrokerOrderResponse],
    summary="Flatten an open position",
)
@inject
async def flatten_position(
    request: Request,
    connection_id: UUID,
    payload: FlattenPositionRequest,
    db: DbSession,
    user: CurrentUser,
    broker_service: BrokerConnectionService = Depends(Provide[Container.broker_service]),
) -> SuccessResponse[BrokerOrderResponse]:
    order = await broker_service.flatten_position(db, user.id, connection_id, payload)
    return success(order, request_id=getattr(request.state, "request_id", None))


@router.post(
    "/connections/{connection_id}/refresh-token",
    response_model=SuccessResponse[BrokerConnectionResponse],
    summary="Refresh OAuth/API token",
)
@inject
async def refresh_broker_token(
    request: Request,
    connection_id: UUID,
    db: DbSession,
    user: CurrentUser,
    broker_service: BrokerConnectionService = Depends(Provide[Container.broker_service]),
) -> SuccessResponse[BrokerConnectionResponse]:
    connection = await broker_service.refresh_token(db, user.id, connection_id)
    return success(connection, request_id=getattr(request.state, "request_id", None))


@router.post(
    "/connections/{connection_id}/validate",
    response_model=SuccessResponse[BrokerHealthResponse],
    summary="Validate broker connection",
)
@inject
async def validate_broker_connection(
    request: Request,
    connection_id: UUID,
    db: DbSession,
    user: CurrentUser,
    broker_service: BrokerConnectionService = Depends(Provide[Container.broker_service]),
) -> SuccessResponse[BrokerHealthResponse]:
    health = await broker_service.validate_connection(db, user.id, connection_id)
    return success(health, request_id=getattr(request.state, "request_id", None))


@router.post(
    "/webhooks/tradingview/{connection_id}",
    response_model=SuccessResponse[BrokerOrderResponse],
    summary="TradingView alert webhook ingress",
    include_in_schema=True,
)
@inject
async def tradingview_webhook(
    request: Request,
    connection_id: UUID,
    db: DbSession,
    broker_service: BrokerConnectionService = Depends(Provide[Container.broker_service]),
    x_tradingview_signature: str | None = Header(default=None, alias="X-TradingView-Signature"),
) -> SuccessResponse[BrokerOrderResponse]:
    body = await request.body()
    payload = json.loads(body.decode() or "{}")
    if not isinstance(payload, dict):
        payload = {}
    order = await broker_service.ingest_tradingview_webhook(
        db,
        connection_id,
        body=body,
        signature=x_tradingview_signature,
        payload=payload,
    )
    return success(order, request_id=getattr(request.state, "request_id", None))
