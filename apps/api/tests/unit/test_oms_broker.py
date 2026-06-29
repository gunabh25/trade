"""OMS and broker SDK unit tests (paper adapter order lifecycle)."""

from __future__ import annotations

from decimal import Decimal

import pytest

from tradeflow.integrations.brokers.adapters.paper import PaperBrokerAdapter
from tradeflow.integrations.brokers.types import (
    BrokerCredentials,
    BrokerOrderSide,
    BrokerOrderStatus,
    BrokerOrderType,
    PlaceOrderRequest,
)


@pytest.fixture
async def paper_broker() -> PaperBrokerAdapter:
    adapter = PaperBrokerAdapter()
    await adapter.connect(
        BrokerCredentials(
            data={
                "account_id": "paper-oms",
                "account_name": "OMS Test",
                "starting_balance": "50000",
            },
        ),
    )
    return adapter


@pytest.mark.unit
@pytest.mark.asyncio
async def test_paper_broker_market_order_fills(
    paper_broker: PaperBrokerAdapter,
) -> None:
    order = await paper_broker.place_order(
        PlaceOrderRequest(
            account_id="paper-oms",
            symbol="ES",
            side=BrokerOrderSide.BUY,
            order_type=BrokerOrderType.MARKET,
            quantity=Decimal("2"),
        ),
    )
    assert order.status == BrokerOrderStatus.FILLED
    assert order.filled_quantity == Decimal("2")

    positions = await paper_broker.fetch_positions("paper-oms")
    assert len(positions) == 1
    assert positions[0].symbol == "ES"
    assert positions[0].quantity == Decimal("2")


@pytest.mark.unit
@pytest.mark.asyncio
async def test_paper_broker_limit_order_stays_open(paper_broker: PaperBrokerAdapter) -> None:
    order = await paper_broker.place_order(
        PlaceOrderRequest(
            account_id="paper-oms",
            symbol="NQ",
            side=BrokerOrderSide.SELL,
            order_type=BrokerOrderType.LIMIT,
            quantity=Decimal("1"),
            price=Decimal("18000"),
        ),
    )
    assert order.status == BrokerOrderStatus.OPEN
    assert order.filled_quantity == Decimal("0")


@pytest.mark.unit
@pytest.mark.asyncio
async def test_paper_broker_cancel_order(paper_broker: PaperBrokerAdapter) -> None:
    order = await paper_broker.place_order(
        PlaceOrderRequest(
            account_id="paper-oms",
            symbol="CL",
            side=BrokerOrderSide.BUY,
            order_type=BrokerOrderType.LIMIT,
            quantity=Decimal("1"),
            price=Decimal("70"),
        ),
    )
    canceled = await paper_broker.cancel_order(order.id)
    assert canceled.status == BrokerOrderStatus.CANCELED


@pytest.mark.unit
@pytest.mark.asyncio
async def test_paper_broker_fetch_accounts(paper_broker: PaperBrokerAdapter) -> None:
    accounts = await paper_broker.fetch_accounts()
    assert len(accounts) == 1
    assert accounts[0].balance == Decimal("50000")
    assert accounts[0].is_live is False
