"""Rithmic R | Protocol client architecture — production wiring pending SDK credentials.

This module defines the connection lifecycle and message routing structure for
Rithmic's binary/protobuf protocol. When production credentials and the official
R | Protocol SDK are provisioned, implement `_connect_socket` and `_send_login`.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any

from tradeflow.core.logging import get_logger
from tradeflow.integrations.brokers.exceptions import BrokerConnectionError, BrokerNotSupportedError

logger = get_logger(__name__)

_RITHMIC_SDK_MSG = (
    "Rithmic R | Protocol SDK integration requires production credentials. "
    "Provide username, password, system_name, and gateway; contact Rithmic for SDK access."
)


class RithmicConnectionState(StrEnum):
    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    AUTHENTICATED = "authenticated"
    READY = "ready"
    ERROR = "error"


@dataclass
class RithmicCredentials:
    username: str
    password: str
    system_name: str
    gateway: str
    app_name: str = "TradeFlowAI"
    app_version: str = "1.0"
    fcm_id: str | None = None
    ib_id: str | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> RithmicCredentials:
        required = ("username", "password", "system_name", "gateway")
        missing = [k for k in required if not data.get(k)]
        if missing:
            msg = f"Missing Rithmic credentials: {', '.join(missing)}"
            raise BrokerConnectionError(msg)
        return cls(
            username=str(data["username"]),
            password=str(data["password"]),
            system_name=str(data["system_name"]),
            gateway=str(data["gateway"]),
            app_name=str(data.get("app_name", cls.app_name)),
            app_version=str(data.get("app_version", cls.app_version)),
            fcm_id=data.get("fcm_id"),
            ib_id=data.get("ib_id"),
        )


@dataclass
class RithmicProtocolClient:
    """Architecture shell for Rithmic R | Protocol WebSocket integration."""

    credentials: RithmicCredentials
    state: RithmicConnectionState = RithmicConnectionState.DISCONNECTED
    _socket: Any = field(default=None, repr=False)
    _subscriptions: list[str] = field(default_factory=list)

    @property
    def gateway_url(self) -> str:
        """Map gateway name to Rithmic endpoint (override when credentials provisioned)."""
        gateway_map = {
            "Chicago": "wss://rprotocol.rithmic.com:443",
            "Tokyo": "wss://rprotocol-tokyo.rithmic.com:443",
            "Frankfurt": "wss://rprotocol-frankfurt.rithmic.com:443",
        }
        return gateway_map.get(self.credentials.gateway, f"wss://{self.credentials.gateway}")

    async def connect(self) -> None:
        """Establish R | Protocol session — raises until SDK credentials are available."""
        self.state = RithmicConnectionState.CONNECTING
        logger.info(
            "rithmic_protocol_connect_attempt",
            system=self.credentials.system_name,
            gateway=self.credentials.gateway,
        )
        raise BrokerNotSupportedError(_RITHMIC_SDK_MSG)

    async def disconnect(self) -> None:
        self.state = RithmicConnectionState.DISCONNECTED
        self._socket = None
        self._subscriptions.clear()

    async def validate_connection(self) -> bool:
        return self.state == RithmicConnectionState.READY

    def build_login_request(self) -> dict[str, Any]:
        """Template login envelope for R | Protocol (implement with official SDK)."""
        return {
            "template_id": 10,
            "user": self.credentials.username,
            "password": "***",
            "system_name": self.credentials.system_name,
            "app_name": self.credentials.app_name,
            "app_version": self.credentials.app_version,
        }

    async def subscribe_market_data(self, symbols: list[str]) -> None:
        self._subscriptions.extend(f"md:{symbol}" for symbol in symbols)
        raise BrokerNotSupportedError(_RITHMIC_SDK_MSG)

    async def subscribe_order_updates(self, account_id: str) -> None:
        self._subscriptions.append(f"orders:{account_id}")
        raise BrokerNotSupportedError(_RITHMIC_SDK_MSG)

    async def subscribe_position_updates(self, account_id: str) -> None:
        self._subscriptions.append(f"positions:{account_id}")
        raise BrokerNotSupportedError(_RITHMIC_SDK_MSG)

    async def place_order(self, payload: dict[str, Any]) -> dict[str, Any]:
        raise BrokerNotSupportedError(_RITHMIC_SDK_MSG)

    async def cancel_order(self, order_id: str) -> dict[str, Any]:
        raise BrokerNotSupportedError(_RITHMIC_SDK_MSG)

    async def flatten_position(self, account_id: str, symbol: str) -> dict[str, Any]:
        raise BrokerNotSupportedError(_RITHMIC_SDK_MSG)
