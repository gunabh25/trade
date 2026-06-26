"""Binance broker adapter."""

from __future__ import annotations

from tradeflow.integrations.brokers.adapters.rest_base import RestBrokerAdapter


class BinanceBrokerAdapter(RestBrokerAdapter):
    @property
    def broker_name(self) -> str:
        return "binance"

    required_credential_keys = ("api_key", "api_secret")
