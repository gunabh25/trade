"""Broker connection business logic."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from tradeflow.core.errors import NotFoundError
from tradeflow.core.logging import get_logger
from tradeflow.core.security.encryption import EncryptionService
from tradeflow.db.enums import (
    BrokerType,
    ConnectionStatus,
    TradingAccountRole,
    TradingAccountStatus,
    TradingAccountType,
    UsageMetric,
)
from tradeflow.db.models.broker import BrokerConnection
from tradeflow.db.models.trading import TradingAccount
from tradeflow.features.broker.schemas import (
    BrokerAccountResponse,
    BrokerCapabilitiesResponse,
    BrokerConnectionResponse,
    BrokerHealthResponse,
    BrokerOrderResponse,
    BrokerPositionResponse,
    CreateBrokerConnectionRequest,
    FlattenPositionRequest,
    ModifyOrderRequest,
    PlaceOrderRequest,
    SupportedBrokersResponse,
    TradingAccountResponse,
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
    ModifyOrderRequest as BrokerModifyOrderRequest,
)
from tradeflow.integrations.brokers.types import (
    PlaceOrderRequest as BrokerPlaceOrderRequest,
)

if TYPE_CHECKING:
    from tradeflow.features.billing.entitlements import EntitlementService

logger = get_logger(__name__)


class BrokerConnectionService:
    """Orchestrates DB persistence and live broker adapter sessions."""

    def __init__(
        self,
        registry: BrokerAdapterRegistry,
        session_manager: BrokerSessionManager,
        encryption_service: EncryptionService,
        entitlements: EntitlementService | None = None,
    ) -> None:
        self._registry = registry
        self._sessions = session_manager
        self._encryption = encryption_service
        self._entitlements = entitlements

    def list_supported_brokers(self) -> SupportedBrokersResponse:
        caps_map = self._registry.capabilities_map()
        capabilities = [
            BrokerCapabilitiesResponse(
                broker=broker,
                supports_rest=caps.supports_rest,
                supports_websocket=caps.supports_websocket,
                supports_stream_market_data=caps.supports_stream_market_data,
                supports_stream_orders=caps.supports_stream_orders,
                supports_stream_positions=caps.supports_stream_positions,
                supports_token_refresh=caps.supports_token_refresh,
                supports_webhook_inbound=caps.supports_webhook_inbound,
                max_orders_per_second=caps.max_orders_per_second,
                supported_asset_classes=list(caps.supported_asset_classes),
                notes=caps.notes,
            )
            for broker, caps in caps_map.items()
        ]
        return SupportedBrokersResponse(
            brokers=[b.value for b in self._registry.supported_brokers()],
            capabilities=capabilities,
        )

    async def create_connection(
        self,
        db: AsyncSession,
        user_id: UUID,
        payload: CreateBrokerConnectionRequest,
    ) -> BrokerConnectionResponse:
        if self._entitlements is not None:
            await self._entitlements.assert_within_limit(
                db,
                user_id,
                UsageMetric.BROKER_CONNECTIONS,
            )
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
        await self.sync_trading_accounts(db, user_id, connection_id)
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

    async def delete_connection(
        self,
        db: AsyncSession,
        user_id: UUID,
        connection_id: UUID,
    ) -> None:
        from tradeflow.core.errors import ConflictError
        from tradeflow.db.models.copy_trading import CopyGroup, CopyGroupFollower

        connection = await self._get_connection(db, user_id, connection_id)
        account_ids = list(
            await db.scalars(
                select(TradingAccount.id).where(
                    TradingAccount.broker_connection_id == connection_id,
                    TradingAccount.user_id == user_id,
                    TradingAccount.deleted_at.is_(None),
                ),
            ),
        )
        if account_ids:
            leader_in_use = await db.scalar(
                select(func.count())
                .select_from(CopyGroup)
                .where(
                    CopyGroup.leader_account_id.in_(account_ids),
                    CopyGroup.deleted_at.is_(None),
                ),
            )
            follower_in_use = await db.scalar(
                select(func.count())
                .select_from(CopyGroupFollower)
                .where(
                    CopyGroupFollower.follower_account_id.in_(account_ids),
                    CopyGroupFollower.deleted_at.is_(None),
                ),
            )
            if int(leader_in_use or 0) > 0 or int(follower_in_use or 0) > 0:
                raise ConflictError(
                    "Remove this connection from copy groups before deleting it",
                )

        await self._sessions.disconnect(connection.id)
        now = datetime.now(tz=UTC)
        connection.deleted_at = now
        accounts = await db.scalars(
            select(TradingAccount).where(
                TradingAccount.broker_connection_id == connection_id,
                TradingAccount.user_id == user_id,
                TradingAccount.deleted_at.is_(None),
            ),
        )
        for account in accounts.all():
            account.deleted_at = now
        await db.flush()
        logger.info("broker_connection_deleted", connection_id=str(connection_id))

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
                side=str(p.side),
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

    async def modify_order(
        self,
        db: AsyncSession,
        user_id: UUID,
        connection_id: UUID,
        order_id: str,
        payload: ModifyOrderRequest,
    ) -> BrokerOrderResponse:
        await self._get_connection(db, user_id, connection_id)
        order = await self._sessions.modify_order(
            connection_id,
            order_id,
            BrokerModifyOrderRequest(
                quantity=payload.quantity,
                price=payload.price,
            ),
        )
        return self._to_order_response(order)

    async def cancel_order(
        self,
        db: AsyncSession,
        user_id: UUID,
        connection_id: UUID,
        order_id: str,
    ) -> BrokerOrderResponse:
        await self._get_connection(db, user_id, connection_id)
        order = await self._sessions.cancel_order(connection_id, order_id)
        return self._to_order_response(order)

    async def flatten_position(
        self,
        db: AsyncSession,
        user_id: UUID,
        connection_id: UUID,
        payload: FlattenPositionRequest,
    ) -> BrokerOrderResponse:
        await self._get_connection(db, user_id, connection_id)
        order = await self._sessions.flatten_position(
            connection_id,
            payload.account_id,
            payload.symbol,
        )
        return self._to_order_response(order)

    async def refresh_token(
        self,
        db: AsyncSession,
        user_id: UUID,
        connection_id: UUID,
    ) -> BrokerConnectionResponse:
        connection = await self._get_connection(db, user_id, connection_id)
        await self._sessions.refresh_token(connection_id)
        return self._to_response(connection)

    async def validate_connection(
        self,
        db: AsyncSession,
        user_id: UUID,
        connection_id: UUID,
    ) -> BrokerHealthResponse:
        connection = await self._get_connection(db, user_id, connection_id)
        valid = await self._sessions.validate_connection(connection_id)
        health = self._sessions.get_health(connection_id)
        if health is None:
            return BrokerHealthResponse(
                connection_id=connection.id,
                status="disconnected" if not valid else "healthy",
                connected=valid,
                websocket_connected=False,
                latency_ms=None,
                reconnect_attempts=0,
                last_error=connection.last_error,
            )
        return self._to_health_response(connection.id, health)

    async def list_trading_accounts(
        self,
        db: AsyncSession,
        user_id: UUID,
    ) -> list[TradingAccountResponse]:
        accounts = await db.scalars(
            select(TradingAccount)
            .join(BrokerConnection)
            .where(
                TradingAccount.user_id == user_id,
                TradingAccount.deleted_at.is_(None),
                BrokerConnection.deleted_at.is_(None),
            )
            .order_by(TradingAccount.created_at.desc()),
        )
        results: list[TradingAccountResponse] = []
        for account in accounts.all():
            connection = await db.get(BrokerConnection, account.broker_connection_id)
            if connection is None:
                continue
            results.append(self._to_trading_account_response(account, connection))
        return results

    async def sync_trading_accounts(
        self,
        db: AsyncSession,
        user_id: UUID,
        connection_id: UUID,
    ) -> list[TradingAccountResponse]:
        connection = await self._get_connection(db, user_id, connection_id)
        broker_accounts = await self._sessions.fetch_accounts(connection_id)

        existing = await db.scalars(
            select(TradingAccount).where(
                TradingAccount.broker_connection_id == connection_id,
                TradingAccount.user_id == user_id,
                TradingAccount.deleted_at.is_(None),
            ),
        )
        existing_by_external = {account.external_account_id: account for account in existing.all()}

        synced: list[TradingAccount] = []
        for broker_account in broker_accounts:
            account = existing_by_external.get(broker_account.id)
            if account is None:
                if self._entitlements is not None:
                    await self._entitlements.assert_within_limit(
                        db,
                        user_id,
                        UsageMetric.TRADING_ACCOUNTS,
                    )
                account = TradingAccount(
                    user_id=user_id,
                    broker_connection_id=connection_id,
                    external_account_id=broker_account.id,
                    name=broker_account.name,
                    account_type=self._resolve_account_type(connection, broker_account.is_live),
                    account_role=TradingAccountRole.UNASSIGNED,
                    status=TradingAccountStatus.ACTIVE,
                    currency=broker_account.currency,
                    balance=broker_account.balance,
                )
                db.add(account)
            else:
                account.name = broker_account.name
                account.balance = broker_account.balance
                account.currency = broker_account.currency
            synced.append(account)

        await db.flush()
        for account in synced:
            await db.refresh(account)

        logger.info(
            "trading_accounts_synced",
            connection_id=str(connection_id),
            count=len(synced),
        )
        return [self._to_trading_account_response(account, connection) for account in synced]

    async def ingest_tradingview_webhook(
        self,
        db: AsyncSession,
        connection_id: UUID,
        *,
        body: bytes,
        signature: str | None,
        payload: dict[str, object],
    ) -> BrokerOrderResponse:
        from tradeflow.integrations.brokers.adapters.tradingview import TradingViewWebhookAdapter

        connection = await db.scalar(
            select(BrokerConnection).where(
                BrokerConnection.id == connection_id,
                BrokerConnection.deleted_at.is_(None),
            ),
        )
        if connection is None:
            raise NotFoundError("Broker connection not found")
        if BrokerType(connection.broker) != BrokerType.TRADINGVIEW:
            raise NotFoundError("Connection is not a TradingView webhook integration")

        adapter = self._sessions.get_adapter(connection_id)
        if adapter is None:
            await self._sessions.connect(
                connection.id,
                BrokerType.TRADINGVIEW,
                connection.credentials_encrypted,
            )
            adapter = self._sessions.get_adapter(connection_id)
        if not isinstance(adapter, TradingViewWebhookAdapter):
            msg = "Invalid TradingView adapter instance"
            raise NotFoundError(msg)

        if not await adapter.validate_webhook_signature(body, signature):
            from tradeflow.core.errors import ForbiddenError

            raise ForbiddenError("Invalid TradingView webhook signature")

        order = await adapter.ingest_webhook(payload)
        connection.last_connected_at = datetime.now(tz=UTC)
        await db.flush()
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
    def _resolve_account_type(connection: BrokerConnection, is_live: bool) -> TradingAccountType:
        broker = BrokerType(connection.broker)
        if broker == BrokerType.PAPER:
            return TradingAccountType.SIM
        return TradingAccountType.LIVE if is_live else TradingAccountType.SIM

    @staticmethod
    def _to_trading_account_response(
        account: TradingAccount,
        connection: BrokerConnection,
    ) -> TradingAccountResponse:
        return TradingAccountResponse(
            id=account.id,
            broker_connection_id=account.broker_connection_id,
            external_account_id=account.external_account_id,
            name=account.name,
            broker=BrokerType(connection.broker),
            account_type=TradingAccountType(account.account_type),
            account_role=TradingAccountRole(account.account_role),
            status=TradingAccountStatus(account.status),
            currency=account.currency,
            balance=account.balance,
            created_at=account.created_at,
        )

    @staticmethod
    def _to_order_response(order: BrokerOrder) -> BrokerOrderResponse:
        return BrokerOrderResponse(
            id=order.id,
            account_id=order.account_id,
            symbol=order.symbol,
            side=str(order.side),
            order_type=str(order.order_type),
            quantity=order.quantity,
            price=order.price,
            status=str(order.status),
            filled_quantity=order.filled_quantity,
        )
