"""Tradovate broker adapter."""

from __future__ import annotations

from tradeflow.integrations.brokers.adapters.rest_base import RestBrokerAdapter


class TradovateBrokerAdapter(RestBrokerAdapter):
    @property
    def broker_name(self) -> str:
        return "tradovate"

    required_credential_keys = ("username", "password")
