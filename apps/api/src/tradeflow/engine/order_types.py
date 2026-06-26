"""Order type normalization between DB, engine, and broker adapters."""

from __future__ import annotations

from tradeflow.db.enums import OrderType
from tradeflow.integrations.brokers.types import BrokerOrderType

# Supported order types for copy engine
SUPPORTED_ORDER_TYPES: frozenset[OrderType] = frozenset(
    {
        OrderType.MARKET,
        OrderType.LIMIT,
        OrderType.STOP,
        OrderType.STOP_LIMIT,
        OrderType.STOP_LOSS,
        OrderType.TAKE_PROFIT,
        OrderType.TRAILING_STOP,
    },
)


def to_broker_order_type(order_type: OrderType) -> BrokerOrderType:
    """Map engine order type to broker adapter order type."""
    mapping: dict[OrderType, BrokerOrderType] = {
        OrderType.MARKET: BrokerOrderType.MARKET,
        OrderType.LIMIT: BrokerOrderType.LIMIT,
        OrderType.STOP: BrokerOrderType.STOP,
        OrderType.STOP_LIMIT: BrokerOrderType.STOP_LIMIT,
        OrderType.STOP_LOSS: BrokerOrderType.STOP_LOSS,
        OrderType.TAKE_PROFIT: BrokerOrderType.TAKE_PROFIT,
        OrderType.TRAILING_STOP: BrokerOrderType.TRAILING_STOP,
    }
    return mapping.get(order_type, BrokerOrderType.MARKET)


def is_bracket_leg(order_type: OrderType) -> bool:
    return order_type in {
        OrderType.STOP_LOSS,
        OrderType.TAKE_PROFIT,
        OrderType.TRAILING_STOP,
    }
