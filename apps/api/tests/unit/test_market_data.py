"""Market data capability and broker SDK tests."""

from __future__ import annotations

import pytest

from tradeflow.db.enums import BrokerType
from tradeflow.integrations.brokers.adapters.paper import PaperBrokerAdapter
from tradeflow.integrations.brokers.exceptions import BrokerNotSupportedError
from tradeflow.integrations.brokers.registry import BrokerAdapterRegistry


@pytest.mark.unit
def test_paper_broker_supports_market_data_stream() -> None:
    adapter = PaperBrokerAdapter()
    assert adapter.capabilities.supports_stream_market_data is True
    assert adapter.capabilities.supports_websocket is True


@pytest.mark.unit
def test_registry_lists_stream_capable_brokers() -> None:
    registry = BrokerAdapterRegistry()
    stream_capable = [
        broker_type
        for broker_type in registry.supported_brokers()
        if registry.create(broker_type).capabilities.supports_stream_market_data
    ]
    assert BrokerType.PAPER in stream_capable
    assert BrokerType.BINANCE in stream_capable


@pytest.mark.unit
@pytest.mark.asyncio
async def test_oanda_does_not_support_market_data_stream() -> None:
    from tradeflow.integrations.brokers.adapters.oanda import OandaBrokerAdapter

    adapter = OandaBrokerAdapter()
    assert adapter.capabilities.supports_stream_market_data is False

    async def handler(_: dict[str, object]) -> None:
        return None

    with pytest.raises(BrokerNotSupportedError):
        await adapter.stream_market_data(["EUR_USD"], handler)
