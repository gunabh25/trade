"""Broker integration exceptions."""

from __future__ import annotations


class BrokerError(Exception):
    """Base broker integration error."""


class BrokerConnectionError(BrokerError):
    """Failed to establish or maintain a connection."""


class BrokerTransientError(BrokerError):
    """Temporary failure suitable for retry."""


class BrokerNotConnectedError(BrokerError):
    """Operation attempted while disconnected."""


class BrokerNotSupportedError(BrokerError):
    """Broker or operation not yet implemented."""


class BrokerOrderError(BrokerError):
    """Order placement, modification, or cancellation failed."""
