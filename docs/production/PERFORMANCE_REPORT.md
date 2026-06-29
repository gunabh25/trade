# Performance Report — Production Optimization

**Date:** June 2026

## Summary

Performance optimizations target the API hot path, database query patterns, Redis memory efficiency, response compression, and horizontal scaling via multi-worker Uvicorn. Existing strengths include SQLAlchemy connection pooling with pre-ping, Redis-backed copy engine caching, and comprehensive database indexes.

## API Performance

### Multi-Worker Process Model

| Setting           | Default (dev) | Production |
| ----------------- | ------------- | ---------- |
| `API_WORKERS`     | 1             | 2+         |
| Graceful shutdown | 30s           | 30s        |
| Proxy headers     | enabled       | enabled    |

Entrypoint: `apps/api/scripts/start.sh`

Use `(2 × CPU cores) + 1` as a starting point for worker count. Monitor memory — each worker holds broker session state.

### Response Compression

- **GZipMiddleware** enabled when `API_ENABLE_GZIP=true` (default)
- Minimum response size: 1 KB
- Next.js `compress: true` for static/SSR responses

Expected savings: 60–80% on JSON payloads > 5 KB.

### Global Rate Limiting

300 requests/minute/IP prevents abuse without impacting normal usage. Returns `429` with `Retry-After` header.

## Database Optimization

### Connection Pool (Existing + Tuned)

```python
pool_size=DATABASE_POOL_SIZE        # prod: 20
max_overflow=DATABASE_MAX_OVERFLOW  # prod: 40
pool_timeout=DATABASE_POOL_TIMEOUT
pool_pre_ping=True                  # drops stale connections
```

### New Indexes (Migration `013_production_indexes`)

| Index                                          | Table                   | Purpose                            |
| ---------------------------------------------- | ----------------------- | ---------------------------------- |
| `ix_notification_deliveries_status_created_at` | notification_deliveries | Admin notification dashboard       |
| `ix_subscriptions_status_deleted_at`           | subscriptions           | Billing/admin subscription queries |
| `ix_usage_records_user_metric_period`          | usage_records           | Usage metering aggregation         |

### Existing Index Coverage

Already indexed across: users, sessions, audit logs, copy trading, orders, trades, positions, risk, journal, billing, broker connections, API keys, notifications.

### Query Recommendations

1. Use pagination on all admin list endpoints (already implemented)
2. Avoid N+1 with `selectinload` (pattern used in admin service)
3. Run `EXPLAIN ANALYZE` on analytics aggregations under load
4. Consider read replica for analytics queries at scale

## Redis Optimization

### Connection Pool (New)

```python
max_connections=REDIS_MAX_CONNECTIONS  # default 50
socket_connect_timeout=5
socket_timeout=5
health_check_interval=30
retry_on_timeout=True
```

### Memory Policy (Production Compose)

```
redis-server --appendonly yes --maxmemory 256mb --maxmemory-policy allkeys-lru
```

### Key Namespace Layout

| Pattern                | Purpose            | TTL        |
| ---------------------- | ------------------ | ---------- |
| `ratelimit:*`          | Rate limiting      | 60s window |
| `auth:lockout:*`       | Login lockout      | 900s       |
| `copy:dedupe:*`        | Copy deduplication | 7 days     |
| `copy:retry:*`         | Retry queue        | varies     |
| `usage:api_requests:*` | Billing meter      | monthly    |
| `user:*:notifications` | Pub/sub            | n/a        |

### Recommendations at Scale

- Monitor memory with `redis.info memory`
- Set explicit TTLs on all cache keys (most already have TTL)
- Consider Redis Cluster when > 1 GB working set

## Caching Strategy

| Layer          | Strategy                       | Status                        |
| -------------- | ------------------------------ | ----------------------------- |
| Copy mappings  | Redis hot + PostgreSQL durable | ✅                            |
| HTTP responses | No cache (auth-sensitive)      | By design                     |
| Analytics      | Computed on demand             | Consider Redis cache at scale |
| Static assets  | Next.js CDN/edge               | Deploy-time                   |

## Prometheus Metrics (New)

| Metric                                    | Type      | Labels               |
| ----------------------------------------- | --------- | -------------------- |
| `tradeflow_http_requests_total`           | Counter   | method, path, status |
| `tradeflow_http_request_duration_seconds` | Histogram | method, path         |
| `tradeflow_http_requests_in_progress`     | Gauge     | —                    |

Scrape: `GET /metrics` every 15s (see `infra/prometheus/prometheus.yml`)

Grafana dashboard: **TradeFlow API** (request rate, p50/p95 latency, 5xx rate, in-flight)

## Celery Performance

- Separate Redis DB for broker (1) and results (2)
- Queues: `default`, `copy`, `risk`, `notifications`, `celery`
- Production: scale workers horizontally (`docker compose scale celery-worker=3`)

## Load Testing Recommendations

Before launch, benchmark:

1. Auth login/register at 50 concurrent users
2. Copy event propagation latency (P50/P95)
3. Admin dashboard with 10k users / 1k subscriptions
4. Stripe webhook burst (replay failed events)

Tools: k6, Locust, or `hey`.

## Performance Checklist

- [ ] Set `API_WORKERS` based on CPU/memory profiling
- [ ] Run `alembic upgrade head` (includes performance indexes)
- [ ] Enable Prometheus + Grafana (`docker-compose.prod.yml`)
- [ ] Monitor p95 latency < 500ms for standard CRUD
- [ ] Monitor copy propagation P95 < 2s (domain SLO)
- [ ] Set Redis `maxmemory` appropriate for workload
- [ ] Enable CDN for Next.js static assets in production

## Profiling & Memory Leak Detection

| Tool             | Usage                                                 |
| ---------------- | ----------------------------------------------------- |
| Sentry Profiling | Set `SENTRY_PROFILES_SAMPLE_RATE=0.1`                 |
| Prometheus       | Watch `tradeflow_http_requests_in_progress` for leaks |
| `tracemalloc`    | Python dev profiling (`python -m tracemalloc`)        |
| Docker stats     | `docker stats` for container memory trends            |

Watch for: growing broker session count, Redis key count without TTL, SQLAlchemy pool exhaustion logs.
