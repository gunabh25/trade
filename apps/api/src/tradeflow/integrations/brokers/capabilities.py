"""Broker capability detection — what each integration supports."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class BrokerCapabilities:
    """Feature flags for a broker integration."""

    supports_rest: bool = True
    supports_websocket: bool = False
    supports_market_orders: bool = True
    supports_limit_orders: bool = True
    supports_stop_orders: bool = False
    supports_modify_order: bool = True
    supports_cancel_order: bool = True
    supports_flatten_position: bool = True
    supports_token_refresh: bool = False
    supports_stream_market_data: bool = False
    supports_stream_orders: bool = False
    supports_stream_positions: bool = False
    supports_webhook_inbound: bool = False
    supports_failover: bool = False
    max_orders_per_second: float = 10.0
    supported_asset_classes: tuple[str, ...] = field(default_factory=lambda: ("equity",))
    notes: str | None = None
