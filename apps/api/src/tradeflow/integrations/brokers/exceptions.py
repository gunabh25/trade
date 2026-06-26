"""Broker integration exceptions."""

from __future__ import annotations

from typing import Any

from tradeflow.integrations.brokers.errors import BrokerErrorCode


class BrokerError(Exception):
    """Base broker integration error."""


class NormalizedBrokerError(BrokerError):
    """Broker error with stable code for upstream handling."""

    def __init__(
        self,
        message: str,
        *,
        code: BrokerErrorCode = BrokerErrorCode.UNKNOWN,
        broker: str | None = None,
        http_status: int | None = None,
        raw: Any = None,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.broker = broker
        self.http_status = http_status
        self.raw = raw


class BrokerConnectionError(NormalizedBrokerError):
    """Failed to establish or maintain a connection."""

    def __init__(self, message: str, **kwargs: Any) -> None:
        kwargs.setdefault("code", BrokerErrorCode.CONNECTION_FAILED)
        super().__init__(message, **kwargs)


class BrokerTransientError(BrokerError):
    """Temporary failure suitable for retry."""


class BrokerNotConnectedError(BrokerError):
    """Operation attempted while disconnected."""


class BrokerNotSupportedError(NormalizedBrokerError):
    """Broker or operation not implemented."""

    def __init__(self, message: str, **kwargs: Any) -> None:
        kwargs.setdefault("code", BrokerErrorCode.NOT_SUPPORTED)
        super().__init__(message, **kwargs)


class BrokerOrderError(NormalizedBrokerError):
    """Order placement, modification, or cancellation failed."""


class BrokerAuthError(NormalizedBrokerError):
    """Authentication or authorization failed."""

    def __init__(self, message: str, **kwargs: Any) -> None:
        kwargs.setdefault("code", BrokerErrorCode.AUTH_FAILED)
        super().__init__(message, **kwargs)


class BrokerRateLimitError(NormalizedBrokerError):
    """Rate limit exceeded."""

    def __init__(self, message: str, **kwargs: Any) -> None:
        kwargs.setdefault("code", BrokerErrorCode.RATE_LIMITED)
        super().__init__(message, **kwargs)
