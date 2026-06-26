import time
import uuid
from collections.abc import Awaitable, Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from tradeflow.core.logging import bind_request_context, clear_request_context, get_logger

logger = get_logger(__name__)


class RequestContextMiddleware(BaseHTTPMiddleware):
    """Attach correlation ID and log request lifecycle."""

    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
        request.state.request_id = request_id

        bind_request_context(
            request_id=request_id,
            method=request.method,
            path=request.url.path,
        )

        start = time.perf_counter()
        status_code = 500

        try:
            response = await call_next(request)
            status_code = response.status_code
            response.headers["X-Request-ID"] = request_id
            return response
        finally:
            duration_ms = round((time.perf_counter() - start) * 1000, 2)
            logger.info(
                "http_request_completed",
                status_code=status_code,
                duration_ms=duration_ms,
            )
            clear_request_context()
