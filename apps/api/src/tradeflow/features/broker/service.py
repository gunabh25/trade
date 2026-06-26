"""Broker connection business logic."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from tradeflow.core.errors import NotFoundError
from tradeflow.core.logging import get_logger
from tradeflow.core.security.encryption import EncryptionService
from tradeflow.db.enums import BrokerType, ConnectionStatus
from tradeflow.db.models.broker import BrokerConnection
from tradeflow.features.broker.schemas import (
    BrokerAccountResponse,
    BrokerConnectionResponse,
    BrokerHealthResponse,
    BrokerOrderResponse,
    BrokerPositionResponse,
    CreateBrokerConnectionRequest,
    PlaceOrderRequest,
    SupportedBrokersResponse,
)
from tradeflow.integrations.brokers.manager import BrokerSessionManager
from tradeflow.integrations.brokers.registry import BrokerAdapterRegistry
from tradeflow.integrations.brokers.types import (
    BrokerOrder,
    BrokerOrderSide,
    BrokerOrderType,
    ConnectionHealth,
)
from tradeflow.integrations.brokers.types import (
    PlaceOrderRequest as BrokerPlaceOrderRequest,
)

logger = get_logger(__name__)


class BrokerConnectionService:
    """Orchestrates DB persistence and live broker adapter sessions."""

    def __init__(
        self,
        registry: BrokerAdapterRegistry,
        session_manager: BrokerSessionManager,
        encryption_service: EncryptionService,
    ) -> None:
        self._registry = registry
        self._sessions = session_manager
        self._encryption = encryption_service

    def list_supported_brokers(self) -> SupportedBrokersResponse:
        return SupportedBrokersResponse(
            brokers=[b.value for b in self._registry.supported_brokers()],
        )

    async def create_connection(
        self,
        db: AsyncSession,
        user_id: UUID,
        payload: CreateBrokerConnectionRequest,
    ) -> BrokerConnectionResponse:
        connection = BrokerConnection(
            user_id=user_id,
            broker=payload.broker,
            name=payload.name,
            status=ConnectionStatus.PENDING,
            credentials_encrypted=self._encryption.encrypt_json(payload.credentials),
        )
        db.add(connection)
        await db.flush()
        await db.refresh(connection)
        logger.info(
            "broker_connection_created",
            connection_id=str(connection.id),
            broker=payload.broker.value,
        )
        return self._to_response(connection)

    async def list_connections(
        self,
        db: AsyncSession,
        user_id: UUID,
    ) -> list[BrokerConnectionResponse]:
        result = await db.scalars(
            select(BrokerConnection).where(
                BrokerConnection.user_id == user_id,
                BrokerConnection.deleted_at.is_(None),
            ),
        )
        return [self._to_response(c) for c in result.all()]

    async def connect(
        self,
        db: AsyncSession,
        user_id: UUID,
        connection_id: UUID,
    ) -> BrokerHealthResponse:
        connection = await self._get_connection(db, user_id, connection_id)
        health = await self._sessions.connect(
            connection.id,
            BrokerType(connection.broker),
            connection.credentials_encrypted,
        )
        connection.status = self._sessions.map_status(health)
        connection.last_connected_at = datetime.now(tz=UTC)
        connection.last_error = health.last_error
        await db.flush()
        return self._to_health_response(connection.id, health)

    async def disconnect(
        self,
        db: AsyncSession,
        user_id: UUID,
        connection_id: UUID,
    ) -> BrokerConnectionResponse:
        connection = await self._get_connection(db, user_id, connection_id)
        await self._sessions.disconnect(connection.id)
        connection.status = ConnectionStatus.DISCONNECTED
        await db.flush()
        return self._to_response(connection)

    async def get_health(
        self,
        db: AsyncSession,
        user_id: UUID,
        connection_id: UUID,
    ) -> BrokerHealthResponse:
        connection = await self._get_connection(db, user_id, connection_id)
        health = self._sessions.get_health(connection.id)
        if health is None:
            return BrokerHealthResponse(
                connection_id=connection.id,
                status="disconnected",
                connected=False,
                websocket_connected=False,
                latency_ms=None,
                reconnect_attempts=0,
                last_error=connection.last_error,
            )
        return self._to_health_response(connection.id, health)

    async def fetch_accounts(
        self,
        db: AsyncSession,
        user_id: UUID,
        connection_id: UUID,
    ) -> list[BrokerAccountResponse]:
        await self._get_connection(db, user_id, connection_id)
        accounts = await self._sessions.fetch_accounts(connection_id)
        return [
            BrokerAccountResponse(
                id=a.id,
                name=a.name,
                currency=a.currency,
                balance=a.balance,
                equity=a.equity,
                is_live=a.is_live,
            )
            for a in accounts
        ]

    async def fetch_orders(
        self,
        db: AsyncSession,
        user_id: UUID,
        connection_id: UUID,
        account_id: str,
    ) -> list[BrokerOrderResponse]:
        await self._get_connection(db, user_id, connection_id)
        orders = await self._sessions.fetch_orders(connection_id, account_id)
        return [self._to_order_response(o) for o in orders]

    async def fetch_positions(
        self,
        db: AsyncSession,
        user_id: UUID,
        connection_id: UUID,
        account_id: str,
    ) -> list[BrokerPositionResponse]:
        await self._get_connection(db, user_id, connection_id)
        positions = await self._sessions.fetch_positions(connection_id, account_id)
        return [
            BrokerPositionResponse(
                id=p.id,
                account_id=p.account_id,
                symbol=p.symbol,
                side=p.side.value,
                quantity=p.quantity,
                entry_price=p.entry_price,
                mark_price=p.mark_price,
                unrealized_pnl=p.unrealized_pnl,
            )
            for p in positions
        ]

    async def place_order(
        self,
        db: AsyncSession,
        user_id: UUID,
        connection_id: UUID,
        payload: PlaceOrderRequest,
    ) -> BrokerOrderResponse:
        await self._get_connection(db, user_id, connection_id)
        order = await self._sessions.place_order(
            connection_id,
            BrokerPlaceOrderRequest(
                account_id=payload.account_id,
                symbol=payload.symbol,
                side=BrokerOrderSide(payload.side),
                order_type=BrokerOrderType(payload.order_type),
                quantity=payload.quantity,
                price=payload.price,
            ),
        )
        return self._to_order_response(order)

    async def _get_connection(
        self,
        db: AsyncSession,
        user_id: UUID,
        connection_id: UUID,
    ) -> BrokerConnection:
        connection = await db.scalar(
            select(BrokerConnection).where(
                BrokerConnection.id == connection_id,
                BrokerConnection.user_id == user_id,
                BrokerConnection.deleted_at.is_(None),
            ),
        )
        if connection is None:
            raise NotFoundError("Broker connection not found")
        return connection

    @staticmethod
    def _to_response(connection: BrokerConnection) -> BrokerConnectionResponse:
        return BrokerConnectionResponse(
            id=connection.id,
            broker=BrokerType(connection.broker),
            name=connection.name,
            status=ConnectionStatus(connection.status),
            last_connected_at=connection.last_connected_at,
            last_error=connection.last_error,
            created_at=connection.created_at,
        )

    @staticmethod
    def _to_health_response(connection_id: UUID, health: ConnectionHealth) -> BrokerHealthResponse:
        return BrokerHealthResponse(
            connection_id=connection_id,
            status=health.status.value,
            connected=health.connected,
            websocket_connected=health.websocket_connected,
            latency_ms=health.latency_ms,
            reconnect_attempts=health.reconnect_attempts,
            last_error=health.last_error,
        )

    @staticmethod
    def _to_order_response(order: BrokerOrder) -> BrokerOrderResponse:
        return BrokerOrderResponse(
            id=order.id,
            account_id=order.account_id,
            symbol=order.symbol,
            side=order.side.value,
            order_type=order.order_type.value,
            quantity=order.quantity,
            price=order.price,
            status=order.status.value,
            filled_quantity=order.filled_quantity,
        )
