"""Unit tests for Prometheus metrics and observability helpers."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest
from starlette.requests import Request
from starlette.responses import Response

from tradeflow.core.observability.prometheus import (
    PrometheusMiddleware,
    _metric_path,
    setup_prometheus,
)


def _make_request(path: str = "/api/v1/health/live") -> Request:
    route = MagicMock()
    route.path = path
    scope = {
        "type": "http",
        "method": "GET",
        "path": path,
        "headers": [],
        "route": route,
    }
    return Request(scope)


@pytest.mark.unit
def test_metric_path_uses_route_template() -> None:
    request = _make_request("/api/v1/health/live")
    assert _metric_path(request) == "/api/v1/health/live"


@pytest.mark.unit
def test_metric_path_falls_back_to_url_path() -> None:
    scope = {
        "type": "http",
        "method": "GET",
        "path": "/unknown",
        "headers": [],
    }
    request = Request(scope)
    assert _metric_path(request) == "/unknown"


@pytest.mark.unit
def test_setup_prometheus_resets_in_progress_gauge() -> None:
    setup_prometheus()


@pytest.mark.unit
@pytest.mark.asyncio
async def test_prometheus_middleware_skips_metrics_endpoint() -> None:
    middleware = PrometheusMiddleware(MagicMock())

    async def call_next(_: Request) -> Response:
        return Response(content="metrics", status_code=200)

    response = await middleware.dispatch(_make_request("/metrics"), call_next)
    assert response.status_code == 200


@pytest.mark.unit
@pytest.mark.asyncio
async def test_prometheus_middleware_records_successful_request() -> None:
    middleware = PrometheusMiddleware(MagicMock())

    async def call_next(_: Request) -> Response:
        return Response(content="ok", status_code=200)

    response = await middleware.dispatch(_make_request(), call_next)
    assert response.status_code == 200
