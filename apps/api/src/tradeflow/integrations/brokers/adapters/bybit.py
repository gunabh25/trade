"""Bybit broker adapter."""

from __future__ import annotations

from tradeflow.integrations.brokers.adapters.rest_base import RestBrokerAdapter


class BybitBrokerAdapter(RestBrokerAdapter):
    @property
    def broker_name(self) -> str:
        return "bybit"

    required_credential_keys = ("api_key", "api_secret")
