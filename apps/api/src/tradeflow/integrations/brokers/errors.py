"""Normalized broker error codes for cross-broker handling."""

from __future__ import annotations

from enum import StrEnum


class BrokerErrorCode(StrEnum):
    """Stable error codes consumed by OMS, copy engine, and UI."""

    UNKNOWN = "unknown"
    AUTH_FAILED = "auth_failed"
    TOKEN_EXPIRED = "token_expired"
    RATE_LIMITED = "rate_limited"
    INSUFFICIENT_FUNDS = "insufficient_funds"
    INVALID_ORDER = "invalid_order"
    ORDER_NOT_FOUND = "order_not_found"
    SYMBOL_NOT_FOUND = "symbol_not_found"
    MARKET_CLOSED = "market_closed"
    CONNECTION_FAILED = "connection_failed"
    TIMEOUT = "timeout"
    NOT_SUPPORTED = "not_supported"
    BROKER_REJECTED = "broker_rejected"
    POSITION_NOT_FOUND = "position_not_found"
