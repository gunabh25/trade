"""Base types for notification channel delivery."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ChannelDeliveryResult:
    """Outcome of a single channel delivery attempt."""

    success: bool
    channel: str
    error: str | None = None
