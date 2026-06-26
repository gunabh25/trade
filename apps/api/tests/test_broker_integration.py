"""Tests for broker integration system."""

from decimal import Decimal

import pytest

from tradeflow.db.enums import BrokerType
from tradeflow.integrations.brokers.adapters.paper import PaperBrokerAdapter
from tradeflow.integrations.brokers.exceptions import BrokerTransientError
from tradeflow.integrations.brokers.registry import BrokerAdapterRegistry
from tradeflow.integrations.brokers.retry import RetryPolicy, with_retry
from tradeflow.integrations.brokers.types import (
    BrokerCredentials,
    BrokerOrderSide,
    BrokerOrderType,
    PlaceOrderRequest,
)


@pytest.mark.asyncio
async def test_paper_broker_connect_and_trade() -> None:
    adapter = PaperBrokerAdapter()
    await adapter.connect(
        BrokerCredentials(
            data={
                "account_id": "paper-1",
                "account_name": "Demo",
                "starting_balance": "50000",
            },
        ),
    )

    accounts = await adapter.fetch_accounts()
    assert len(accounts) == 1
    assert accounts[0].equity == Decimal("50000")

    order = await adapter.place_order(
        PlaceOrderRequest(
            account_id="paper-1",
            symbol="ES",
            side=BrokerOrderSide.BUY,
            order_type=BrokerOrderType.MARKET,
            quantity=Decimal("2"),
        ),
    )
    assert order.status.value == "filled"

    positions = await adapter.fetch_positions("paper-1")
    assert len(positions) == 1
    assert positions[0].symbol == "ES"

    health = adapter.get_health()
    assert health.connected is True

    await adapter.disconnect()
    assert adapter.get_health().connected is False


@pytest.mark.asyncio
async def test_retry_recovers_from_transient_error() -> None:
    attempts = 0

    async def flaky() -> str:
        nonlocal attempts
        attempts += 1
        if attempts < 3:
            raise BrokerTransientError("temporary")
        return "ok"

    result = await with_retry(
        flaky,
        policy=RetryPolicy(max_attempts=3, base_delay_seconds=0),
        operation_name="test",
    )
    assert result == "ok"
    assert attempts == 3


def test_registry_supports_all_brokers() -> None:
    registry = BrokerAdapterRegistry()
    supported = set(registry.supported_brokers())
    expected = {
        BrokerType.PAPER,
        BrokerType.BINANCE,
        BrokerType.BYBIT,
        BrokerType.OANDA,
        BrokerType.INTERACTIVE_BROKERS,
        BrokerType.TRADOVATE,
        BrokerType.TRADINGVIEW,
        BrokerType.RITHMIC,
    }
    assert expected.issubset(supported)

    paper = registry.create(BrokerType.PAPER)
    assert paper.broker_name == "paper"
