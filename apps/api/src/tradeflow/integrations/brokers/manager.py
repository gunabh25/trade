"""Runtime broker session manager."""

from __future__ import annotations

from uuid import UUID

from tradeflow.core.logging import get_logger
from tradeflow.core.security.encryption import EncryptionService
from tradeflow.db.enums import BrokerType, ConnectionStatus
from tradeflow.integrations.brokers.interface import BrokerAdapter
from tradeflow.integrations.brokers.monitor import ConnectionMonitor
from tradeflow.integrations.brokers.registry import BrokerAdapterRegistry
from tradeflow.integrations.brokers.types import (
    BrokerAccount,
    BrokerCredentials,
    BrokerHealthStatus,
    BrokerOrder,
    BrokerPosition,
    ConnectionHealth,
    ModifyOrderRequest,
    PlaceOrderRequest,
)

logger = get_logger(__name__)


class BrokerSessionManager:
    """Manages live adapter instances keyed by connection ID."""

    def __init__(
        self,
        registry: BrokerAdapterRegistry,
        monitor: ConnectionMonitor,
        encryption_service: EncryptionService,
    ) -> None:
        self._registry = registry
        self._monitor = monitor
        self._encryption = encryption_service
        self._sessions: dict[UUID, BrokerAdapter] = {}

    async def connect(
        self,
        connection_id: UUID,
        broker_type: BrokerType,
        credentials_encrypted: str,
    ) -> ConnectionHealth:
        credentials_json = self._encryption.decrypt_json(credentials_encrypted)
        adapter = self._registry.create(broker_type)
        await adapter.connect(BrokerCredentials(data=credentials_json))
        self._sessions[connection_id] = adapter
        self._monitor.register(connection_id, adapter)
        health = adapter.get_health()
        logger.info(
            "broker_session_connected",
            connection_id=str(connection_id),
            broker=broker_type.value,
        )
        return health

    async def disconnect(self, connection_id: UUID) -> None:
        adapter = self._sessions.pop(connection_id, None)
        if adapter is None:
            return
        await adapter.disconnect()
        self._monitor.unregister(connection_id)
        logger.info("broker_session_disconnected", connection_id=str(connection_id))

    async def disconnect_all(self) -> None:
        """Gracefully tear down all live broker sessions on shutdown."""
        for connection_id in list(self._sessions.keys()):
            await self.disconnect(connection_id)

    def get_adapter(self, connection_id: UUID) -> BrokerAdapter | None:
        return self._sessions.get(connection_id)

    async def fetch_accounts(self, connection_id: UUID) -> list[BrokerAccount]:
        adapter = self._require_adapter(connection_id)
        return await adapter.fetch_accounts()

    async def fetch_orders(self, connection_id: UUID, account_id: str) -> list[BrokerOrder]:
        adapter = self._require_adapter(connection_id)
        return await adapter.fetch_orders(account_id)

    async def fetch_positions(
        self,
        connection_id: UUID,
        account_id: str,
    ) -> list[BrokerPosition]:
        adapter = self._require_adapter(connection_id)
        return await adapter.fetch_positions(account_id)

    async def place_order(self, connection_id: UUID, request: PlaceOrderRequest) -> BrokerOrder:
        adapter = self._require_adapter(connection_id)
        return await adapter.place_order(request)

    async def modify_order(
        self,
        connection_id: UUID,
        order_id: str,
        request: ModifyOrderRequest,
    ) -> BrokerOrder:
        adapter = self._require_adapter(connection_id)
        return await adapter.modify_order(order_id, request)

    async def cancel_order(self, connection_id: UUID, order_id: str) -> BrokerOrder:
        adapter = self._require_adapter(connection_id)
        return await adapter.cancel_order(order_id)

    def get_health(self, connection_id: UUID) -> ConnectionHealth | None:
        adapter = self._sessions.get(connection_id)
        if adapter is None:
            return self._monitor.get_health(connection_id)
        return adapter.get_health()

    def _require_adapter(self, connection_id: UUID) -> BrokerAdapter:
        adapter = self._sessions.get(connection_id)
        if adapter is None:
            msg = f"No active session for connection {connection_id}"
            raise ValueError(msg)
        return adapter

    @staticmethod
    def map_status(health: ConnectionHealth) -> ConnectionStatus:
        if health.connected and health.status == BrokerHealthStatus.HEALTHY:
            return ConnectionStatus.CONNECTED
        if health.status == BrokerHealthStatus.ERROR:
            return ConnectionStatus.ERROR
        return ConnectionStatus.DISCONNECTED
