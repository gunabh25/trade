"""Prometheus metrics exposition for production monitoring."""

from __future__ import annotations

import time
from collections.abc import Awaitable, Callable

from fastapi import APIRouter, Request, Response
from prometheus_client import (
    CONTENT_TYPE_LATEST,
    Counter,
    Gauge,
    Histogram,
    generate_latest,
)
from starlette.middleware.base import BaseHTTPMiddleware

HTTP_REQUESTS_TOTAL = Counter(
    "tradeflow_http_requests_total",
    "Total HTTP requests",
    ["method", "path", "status"],
)

HTTP_REQUEST_DURATION_SECONDS = Histogram(
    "tradeflow_http_request_duration_seconds",
    "HTTP request latency in seconds",
    ["method", "path"],
    buckets=(0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0),
)

HTTP_REQUESTS_IN_PROGRESS = Gauge(
    "tradeflow_http_requests_in_progress",
    "In-flight HTTP requests",
)

metrics_router = APIRouter(tags=["Metrics"])


def setup_prometheus() -> None:
    """Register process-level collectors (invoked once at startup)."""
    # prometheus_client auto-registers process/platform collectors on import.
    HTTP_REQUESTS_IN_PROGRESS.set(0)


def _metric_path(request: Request) -> str:
    route = request.scope.get("route")
    if route is not None and hasattr(route, "path"):
        return route.path
    return request.url.path


@metrics_router.get("/metrics", include_in_schema=False)
async def prometheus_metrics() -> Response:
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)


class PrometheusMiddleware(BaseHTTPMiddleware):
    """Record request counts and latency histograms for Prometheus."""

    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        if request.url.path == "/metrics":
            return await call_next(request)

        method = request.method
        path = _metric_path(request)
        HTTP_REQUESTS_IN_PROGRESS.inc()
        start = time.perf_counter()
        status_code = 500

        try:
            response = await call_next(request)
            status_code = response.status_code
            return response
        finally:
            duration = time.perf_counter() - start
            HTTP_REQUESTS_IN_PROGRESS.dec()
            HTTP_REQUEST_DURATION_SECONDS.labels(method=method, path=path).observe(duration)
            HTTP_REQUESTS_TOTAL.labels(
                method=method,
                path=path,
                status=str(status_code),
            ).inc()
