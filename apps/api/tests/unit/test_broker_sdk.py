"""Broker SDK unit tests."""

from __future__ import annotations

import pytest

from tradeflow.integrations.brokers.exceptions import BrokerConnectionError, BrokerNotSupportedError
from tradeflow.integrations.brokers.sdk.binance_stream import BinanceStreamClient
from tradeflow.integrations.brokers.sdk.bybit_stream import BybitStreamClient
from tradeflow.integrations.brokers.sdk.normalizers import (
    normalize_market_event,
    normalize_order_event,
    normalize_position_event,
)
from tradeflow.integrations.brokers.sdk.rithmic_protocol import (
    RithmicCredentials,
    RithmicProtocolClient,
)


def test_normalize_binance_execution_report() -> None:
    event = normalize_order_event(
        "binance",
        {
            "e": "executionReport",
            "i": 123,
            "s": "BTCUSDT",
            "S": "BUY",
            "X": "FILLED",
            "q": "0.1",
            "z": "0.1",
        },
    )
    assert event["type"] == "order"
    assert event["symbol"] == "BTCUSDT"
    assert event["status"] == "filled"


def test_normalize_bybit_position() -> None:
    event = normalize_position_event(
        "bybit",
        {
            "topic": "position",
            "data": [
                {
                    "symbol": "BTCUSDT",
                    "side": "Buy",
                    "size": "1",
                    "avgPrice": "50000",
                    "markPrice": "50100",
                    "unrealisedPnl": "100",
                },
            ],
        },
    )
    assert event["type"] == "position"
    assert event["symbol"] == "BTCUSDT"


def test_normalize_binance_trade_quote() -> None:
    event = normalize_market_event(
        "binance",
        {"e": "trade", "s": "ETHUSDT", "p": "3000", "q": "0.5", "T": 1234567890},
    )
    assert event["type"] == "quote"
    assert event["symbol"] == "ETHUSDT"


def test_binance_stream_market_url() -> None:
    client = BinanceStreamClient(api_key="k", signed_post=lambda *_: None)
    url = client.market_stream_url(["BTCUSDT", "ETHUSDT"])
    assert "btcusdt" in url
    assert "ethusdt" in url
    assert "trade" in url


def test_bybit_auth_payload_shape() -> None:
    client = BybitStreamClient(api_key="key", api_secret="secret")
    payload = client.auth_payload()
    assert payload["op"] == "auth"
    assert len(payload["args"]) == 3


def test_rithmic_credentials_validation() -> None:
    with pytest.raises(BrokerConnectionError):
        RithmicCredentials.from_dict({"username": "u"})


@pytest.mark.asyncio
async def test_rithmic_protocol_connect_raises_without_sdk() -> None:
    client = RithmicProtocolClient(
        credentials=RithmicCredentials(
            username="u",
            password="p",
            system_name="Rithmic Paper",
            gateway="Chicago",
        ),
    )
    with pytest.raises(BrokerNotSupportedError):
        await client.connect()


def test_rithmic_login_request_template() -> None:
    client = RithmicProtocolClient(
        credentials=RithmicCredentials(
            username="u",
            password="p",
            system_name="Rithmic Paper",
            gateway="Chicago",
        ),
    )
    login = client.build_login_request()
    assert login["template_id"] == 10
    assert login["system_name"] == "Rithmic Paper"
