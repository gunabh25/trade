# Broker Integration Layer

Production broker adapters for TradeFlow AI. Every integration implements the full `BrokerAdapter` contract with automatic reconnect, retry, rate limiting, error normalization, metrics, and capability detection.

## Architecture

```
integrations/brokers/
├── interface.py          # BrokerAdapter contract
├── base.py                 # Lifecycle, retry, metrics, reconnect
├── capabilities.py         # Feature detection per broker
├── sdk/                    # Low-level WebSocket/protocol clients
│   ├── binance_stream.py   # Binance user-data + combined streams
│   ├── bybit_stream.py     # Bybit V5 private/public WS auth
│   ├── normalizers.py      # Stream event normalization
│   └── rithmic_protocol.py # R | Protocol architecture shell
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

| Broker                  | Status               | Auth                             | Notes                                    |
| ----------------------- | -------------------- | -------------------------------- | ---------------------------------------- |
| **Paper**               | Full                 | None                             | In-memory simulation                     |
| **Binance**             | Production REST + WS | API key + HMAC secret            | Spot API, user-data stream, testnet      |
| **Bybit**               | Production REST + WS | API key + HMAC secret            | V5 unified account, private WS           |
| **OANDA**               | Production REST      | Bearer token                     | Practice/live environments               |
| **Interactive Brokers** | Production REST      | Client Portal                    | Requires IB Gateway :5000                |
| **Tradovate**           | Production REST      | Username/password OAuth          | Token refresh supported                  |
| **TradingView**         | Webhook inbound      | HMAC webhook secret              | `POST /broker/webhooks/tradingview/{id}` |
| **Rithmic**             | Protocol shell       | username/password/system/gateway | SDK wiring pending                       |

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

## REST API

| Method | Path                                                  | Description                      |
| ------ | ----------------------------------------------------- | -------------------------------- |
| GET    | `/api/v1/broker/supported`                            | List brokers + capability matrix |
| POST   | `/api/v1/broker/connections/{id}/orders`              | Place order                      |
| PATCH  | `/api/v1/broker/connections/{id}/orders/{order_id}`   | Modify order                     |
| DELETE | `/api/v1/broker/connections/{id}/orders/{order_id}`   | Cancel order                     |
| POST   | `/api/v1/broker/connections/{id}/flatten`             | Flatten position                 |
| POST   | `/api/v1/broker/connections/{id}/refresh-token`       | Refresh OAuth token              |
| POST   | `/api/v1/broker/connections/{id}/validate`            | Validate connection              |
| POST   | `/api/v1/broker/webhooks/tradingview/{connection_id}` | TradingView alert ingress        |

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
pytest tests/test_broker_integration.py tests/test_broker_adapters.py tests/unit/test_broker_sdk.py -v
```

Integration tests use mocked HTTP — no live API keys required.

## WebSocket Streaming

Adapters with streaming capabilities use the `sdk/` WebSocket clients:

- **Binance** — listen-key user data stream for orders; combined stream for quotes
- **Bybit** — V5 private WS auth for orders/positions; public linear tickers
- **Paper / TradingView** — in-process event bus via `BrokerWebSocketManager`

Stream payloads are normalized via `sdk/normalizers.py` to `{type: order|position|quote, ...}`.

TradingView webhook endpoint (no session cookie required; HMAC validated):

```http
POST /api/v1/broker/webhooks/tradingview/{connection_id}
X-TradingView-Signature: <hmac-sha256-hex>
Content-Type: application/json

{"action": "buy", "symbol": "ES", "quantity": "1"}
```
