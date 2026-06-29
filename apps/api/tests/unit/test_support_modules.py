"""Unit tests for test factories and mocks."""

from __future__ import annotations

from decimal import Decimal

import pytest
from tests.support.factories import (
    follower_context,
    leader_event,
    proposed_order,
    register_payload,
    unique_email,
)
from tests.support.mocks import MockEmailService, MockStripeClient, mock_broker_adapter

from tradeflow.db.enums import CopyMode, OrderSide


@pytest.mark.unit
def test_unique_email_generates_valid_addresses() -> None:
    a = unique_email("trader")
    b = unique_email("trader")
    assert a != b
    assert a.endswith("@example.com")


@pytest.mark.unit
def test_register_payload_has_required_fields() -> None:
    payload = register_payload()
    assert "email" in payload
    assert len(payload["password"]) >= 8


@pytest.mark.unit
def test_leader_event_factory_defaults() -> None:
    event = leader_event()
    assert event.symbol == "ES"
    assert event.quantity == 2
    assert event.side == OrderSide.BUY


@pytest.mark.unit
def test_follower_context_fixed_quantity() -> None:
    ctx = follower_context(copy_mode=CopyMode.FIXED_QUANTITY, sizing_value=Decimal("3"))
    assert ctx.copy_mode == CopyMode.FIXED_QUANTITY
    assert ctx.sizing_value == Decimal("3")


@pytest.mark.unit
def test_proposed_order_factory() -> None:
    order = proposed_order(symbol="NQ", quantity=5)
    assert order.symbol == "NQ"
    assert order.quantity == 5


@pytest.mark.unit
@pytest.mark.asyncio
async def test_mock_email_service_records_sends() -> None:
    svc = MockEmailService()
    await svc.send_password_reset(to="u@test.com", reset_url="https://example.com/reset")
    assert len(svc.sent) == 1
    assert svc.sent[0]["type"] == "password_reset"


@pytest.mark.unit
def test_mock_stripe_client_checkout() -> None:
    stripe = MockStripeClient()
    url = stripe.create_checkout_session(customer_id="cus_test", price_id="price_pro")
    assert "checkout.stripe.test" in url
    assert len(stripe.checkout_sessions) == 1


@pytest.mark.unit
def test_mock_broker_adapter_health() -> None:
    adapter = mock_broker_adapter(connected=True)
    health = adapter.get_health()
    assert health.connected is True
