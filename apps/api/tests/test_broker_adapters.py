"""Production broker adapter tests with mocked HTTP."""

from __future__ import annotations

from decimal import Decimal
from unittest.mock import AsyncMock, patch

import pytest

from tradeflow.db.enums import BrokerType
from tradeflow.integrations.brokers.adapters.binance import BinanceBrokerAdapter
from tradeflow.integrations.brokers.adapters.rithmic import RithmicBrokerAdapter
from tradeflow.integrations.brokers.adapters.tradingview import TradingViewWebhookAdapter
from tradeflow.integrations.brokers.capabilities import BrokerCapabilities
from tradeflow.integrations.brokers.exceptions import BrokerConnectionError, BrokerNotSupportedError
from tradeflow.integrations.brokers.http_client import BrokerHttpClient
from tradeflow.integrations.brokers.registry import BrokerAdapterRegistry
from tradeflow.integrations.brokers.types import BrokerCredentials


@pytest.mark.asyncio
async def test_tradingview_webhook_ingest() -> None:
    adapter = TradingViewWebhookAdapter()
    await adapter.connect(BrokerCredentials(data={"webhook_secret": "test-secret"}))
    order = await adapter.ingest_webhook(
        {"action": "buy", "symbol": "ES", "quantity": "2"},
    )
    assert order.symbol == "ES"
    assert order.side.value == "buy"
    assert order.quantity == Decimal("2")
    orders = await adapter.fetch_orders("tradingview-default")
    assert len(orders) == 1


@pytest.mark.asyncio
async def test_tradingview_requires_secret() -> None:
    adapter = TradingViewWebhookAdapter()
    with pytest.raises(BrokerConnectionError):
        await adapter.connect(BrokerCredentials(data={}))


@pytest.mark.asyncio
async def test_rithmic_requires_credentials() -> None:
    adapter = RithmicBrokerAdapter()
    with pytest.raises(BrokerConnectionError):
        await adapter.connect(BrokerCredentials(data={"username": "u"}))


@pytest.mark.asyncio
async def test_rithmic_operations_not_supported_with_full_creds() -> None:
    adapter = RithmicBrokerAdapter()
    creds = BrokerCredentials(
        data={
            "username": "u",
            "password": "p",
            "system_name": "Rithmic Paper",
            "gateway": "Chicago",
        },
    )
    with pytest.raises(BrokerNotSupportedError):
        await adapter.connect(creds)


@pytest.mark.asyncio
async def test_binance_validate_connection() -> None:
    adapter = BinanceBrokerAdapter()
    await adapter.connect(
        BrokerCredentials(
            data={"api_key": "key", "api_secret": "secret", "testnet": True},
        ),
    )
    with patch.object(adapter, "_signed_request", new_callable=AsyncMock) as mock_req:
        mock_req.return_value = {}
        assert await adapter.validate_connection() is True


@pytest.mark.asyncio
async def test_binance_fetch_accounts_parses_balances() -> None:
    adapter = BinanceBrokerAdapter()
    await adapter.connect(
        BrokerCredentials(
            data={"api_key": "key", "api_secret": "secret", "testnet": True},
        ),
    )
    with patch.object(adapter, "_signed_request", new_callable=AsyncMock) as mock_req:
        mock_req.return_value = {
            "accountType": "SPOT",
            "canTrade": True,
            "balances": [
                {"asset": "BTC", "free": "1.0", "locked": "0"},
                {"asset": "USDT", "free": "1000", "locked": "0"},
            ],
        }
        accounts = await adapter.fetch_accounts()
        assert len(accounts) == 1
        assert accounts[0].balance > 0


def test_registry_includes_rithmic() -> None:
    registry = BrokerAdapterRegistry()
    assert BrokerType.RITHMIC in registry.supported_brokers()


def test_capabilities_detection() -> None:
    caps = BrokerCapabilities(
        supports_token_refresh=True,
        supports_stream_orders=True,
    )
    assert caps.supports_token_refresh is True
    assert caps.supports_stream_orders is True


def test_http_client_normalizes_rate_limit() -> None:
    import httpx

    from tradeflow.integrations.brokers.exceptions import BrokerRateLimitError
    from tradeflow.integrations.brokers.pool import BrokerHttpPool
    from tradeflow.integrations.brokers.rate_limit import TokenBucketRateLimiter

    client = BrokerHttpClient(
        broker_name="test",
        pool=BrokerHttpPool(base_url="https://example.com"),
        rate_limiter=TokenBucketRateLimiter(rate_per_second=100),
    )

    response = httpx.Response(429, json={"msg": "rate limit"})
    with pytest.raises(BrokerRateLimitError):
        client._normalize_response(response)
