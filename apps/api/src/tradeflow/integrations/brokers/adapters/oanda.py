"""OANDA broker adapter."""

from __future__ import annotations

from tradeflow.integrations.brokers.adapters.rest_base import RestBrokerAdapter


class OandaBrokerAdapter(RestBrokerAdapter):
    @property
    def broker_name(self) -> str:
        return "oanda"

    required_credential_keys = ("api_key", "account_id")
