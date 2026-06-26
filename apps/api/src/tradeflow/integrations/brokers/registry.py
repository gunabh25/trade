"""Broker adapter registry — Open/Closed: register new brokers without modifying consumers."""

from __future__ import annotations

from collections.abc import Callable

from tradeflow.db.enums import BrokerType
from tradeflow.integrations.brokers.adapters.binance import BinanceBrokerAdapter
from tradeflow.integrations.brokers.adapters.bybit import BybitBrokerAdapter
from tradeflow.integrations.brokers.adapters.interactive_brokers import InteractiveBrokersAdapter
from tradeflow.integrations.brokers.adapters.oanda import OandaBrokerAdapter
from tradeflow.integrations.brokers.adapters.paper import PaperBrokerAdapter
from tradeflow.integrations.brokers.adapters.tradingview import TradingViewWebhookAdapter
from tradeflow.integrations.brokers.adapters.tradovate import TradovateBrokerAdapter
from tradeflow.integrations.brokers.interface import BrokerAdapter
from tradeflow.integrations.brokers.retry import RetryPolicy

AdapterFactory = Callable[[], BrokerAdapter]


class BrokerAdapterRegistry:
    """Factory registry mapping BrokerType → adapter instance."""

    def __init__(self, retry_policy: RetryPolicy | None = None) -> None:
        self._retry_policy = retry_policy or RetryPolicy()
        self._factories: dict[BrokerType, AdapterFactory] = {}
        self._register_defaults()

    def register(self, broker_type: BrokerType, factory: AdapterFactory) -> None:
        self._factories[broker_type] = factory

    def create(self, broker_type: BrokerType) -> BrokerAdapter:
        factory = self._factories.get(broker_type)
        if factory is None:
            msg = f"No adapter registered for broker type: {broker_type.value}"
            raise ValueError(msg)
        return factory()

    def supported_brokers(self) -> list[BrokerType]:
        return list(self._factories.keys())

    def _register_defaults(self) -> None:
        policy = self._retry_policy

        def _with_policy(cls: type[BrokerAdapter]) -> AdapterFactory:
            return lambda: cls(retry_policy=policy)  # type: ignore[call-arg]

        self.register(BrokerType.PAPER, _with_policy(PaperBrokerAdapter))
        self.register(BrokerType.BINANCE, _with_policy(BinanceBrokerAdapter))
        self.register(BrokerType.BYBIT, _with_policy(BybitBrokerAdapter))
        self.register(BrokerType.OANDA, _with_policy(OandaBrokerAdapter))
        self.register(BrokerType.INTERACTIVE_BROKERS, _with_policy(InteractiveBrokersAdapter))
        self.register(BrokerType.TRADOVATE, _with_policy(TradovateBrokerAdapter))
        self.register(BrokerType.TRADINGVIEW, _with_policy(TradingViewWebhookAdapter))
