# Broker Integration Layer

Production broker adapters for TradeFlow AI. Every integration implements the full `BrokerAdapter` contract with automatic reconnect, retry, rate limiting, error normalization, metrics, and capability detection.

## Architecture

```
integrations/brokers/
├── interface.py          # BrokerAdapter contract
├── base.py                 # Lifecycle, retry, metrics, reconnect
├── capabilities.py         # Feature detection per broker
├── errors.py               # Normalized error codes
├── exceptions.py           # Typed exceptions
├── http_client.py          # Pooled HTTP + error normalization
├── pool.py                 # httpx connection pooling
├── rate_limit.py           # Token-bucket rate limiter
├── metrics.py              # Operation latency/error metrics
├── retry.py                # Exponential backoff
├── websocket.py            # WebSocket manager with reconnect
├── failover.py             # Primary/secondary failover wrapper
└── adapters/
    ├── rest_base.py        # REST adapter base
    ├── binance.py          # Binance Spot API
    ├── bybit.py            # Bybit V5 API
    ├── oanda.py            # OANDA v20 REST
    ├── interactive_brokers.py  # IB Client Portal API
    ├── tradovate.py        # Tradovate OAuth + REST
    ├── tradingview.py      # Webhook inbound signals
    ├── rithmic.py          # Rithmic stub (credentials required)
    └── paper.py            # In-memory simulation
```

## BrokerAdapter Contract

Every adapter implements:

| Method                  | Description                         |
| ----------------------- | ----------------------------------- |
| `connect()`             | Authenticate and establish sessions |
| `disconnect()`          | Tear down HTTP pool and WebSockets  |
| `refresh_token()`       | OAuth token renewal (Tradovate)     |
| `validate_connection()` | Lightweight health ping             |
| `fetch_accounts()`      | List trading accounts               |
| `fetch_orders()`        | Open/recent orders                  |
| `fetch_positions()`     | Open positions                      |
| `place_order()`         | Submit order                        |
| `modify_order()`        | Amend working order                 |
| `cancel_order()`        | Cancel order                        |
| `flatten_position()`    | Market-close entire position        |
| `stream_market_data()`  | Real-time quotes via WebSocket      |
| `stream_orders()`       | Order update stream                 |
| `stream_positions()`    | Position update stream              |
| `capabilities`          | Feature flags for this broker       |

## Supported Brokers

| Broker                  | Status          | Auth                             | Notes                       |
| ----------------------- | --------------- | -------------------------------- | --------------------------- |
| **Paper**               | Full            | None                             | In-memory simulation        |
| **Binance**             | Production REST | API key + HMAC secret            | Spot API, testnet supported |
| **Bybit**               | Production REST | API key + HMAC secret            | V5 unified account          |
| **OANDA**               | Production REST | Bearer token                     | Practice/live environments  |
| **Interactive Brokers** | Production REST | Client Portal                    | Requires IB Gateway :5000   |
| **Tradovate**           | Production REST | Username/password OAuth          | Token refresh supported     |
| **TradingView**         | Webhook inbound | HMAC webhook secret              | Use `ingest_webhook()`      |
| **Rithmic**             | Interface only  | username/password/system/gateway | Pending R \| Protocol SDK   |

## Credentials

### Binance

```json
{
  "api_key": "...",
  "api_secret": "...",
  "testnet": true,
  "default_symbol": "BTCUSDT"
}
```

### Bybit

```json
{
  "api_key": "...",
  "api_secret": "...",
  "testnet": false
}
```

### OANDA

```json
{
  "api_key": "...",
  "account_id": "...",
  "practice": true
}
```

### Interactive Brokers

```json
{
  "account_id": "U1234567",
  "base_url": "https://localhost:5000/v1/api"
}
```

### Tradovate

```json
{
  "username": "...",
  "password": "...",
  "demo": false,
  "app_id": "TradeFlow",
  "cid": 0,
  "sec": "..."
}
```

### TradingView

```json
{
  "webhook_secret": "...",
  "account_id": "tv-signals-1"
}
```

### Rithmic (when available)

```json
{
  "username": "...",
  "password": "...",
  "system_name": "Rithmic Paper Trading",
  "gateway": "Chicago Area"
}
```

## Error Normalization

All HTTP adapters map broker responses to stable codes:

| Code                 | Meaning               |
| -------------------- | --------------------- |
| `auth_failed`        | Invalid credentials   |
| `rate_limited`       | HTTP 429              |
| `insufficient_funds` | Margin/balance error  |
| `invalid_order`      | Rejected order params |
| `order_not_found`    | Unknown order ID      |
| `connection_failed`  | Network/timeout       |
| `not_supported`      | Operation unavailable |

## Failover

Wrap any two adapters:

```python
from tradeflow.integrations.brokers.failover import FailoverBrokerAdapter

adapter = FailoverBrokerAdapter(primary=binance, secondary=bybit)
await adapter.connect(credentials)
```

On connection failure, operations automatically route to the secondary adapter.

## Metrics

Operation latency and error counts are recorded in-process:

```python
from tradeflow.integrations.brokers.metrics import get_broker_metrics

get_broker_metrics().snapshot()
# {"binance.place_order": {"count": 42, "errors": 1, "avg_latency_ms": 120.5}}
```

## Testing

```bash
cd apps/api
pytest tests/test_broker_integration.py tests/test_broker_adapters.py -v
```

Integration tests use mocked HTTP — no live API keys required.

## WebSocket Streaming

Adapters with `capabilities.supports_stream_orders = True` expose real-time streams via `stream_orders()`. The WebSocket manager uses the `websockets` library with automatic reconnect on disconnect.

TradingView emits order events when webhooks are ingested:

```python
adapter = TradingViewWebhookAdapter()
await adapter.connect(BrokerCredentials(data={"webhook_secret": "..."}))
sub = await adapter.stream_orders("default", my_handler)
await adapter.ingest_webhook({"action": "buy", "symbol": "ES", "quantity": "1"})
```
