"""Interactive Brokers adapter."""

from __future__ import annotations

from tradeflow.integrations.brokers.adapters.rest_base import RestBrokerAdapter


class InteractiveBrokersAdapter(RestBrokerAdapter):
    @property
    def broker_name(self) -> str:
        return "interactive_brokers"

    required_credential_keys = ("username", "account_id")
