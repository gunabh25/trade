from typing import Any, cast

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import ValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

from tradeflow.core.errors import AppError, ErrorCode
from tradeflow.core.logging import get_logger

logger = get_logger(__name__)


def _error_payload(
    code: ErrorCode,
    message: str,
    *,
    details: list[dict[str, Any]] | None = None,
    request_id: str | None = None,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "error": {
            "code": code.value,
            "message": message,
        }
    }
    if details:
        payload["error"]["details"] = details
    if request_id:
        payload["error"]["requestId"] = request_id
    return payload


async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
    request_id: str | None = getattr(request.state, "request_id", None)
    logger.warning(
        "application_error",
        code=exc.code.value,
        message=exc.message,
        status_code=exc.status_code,
        request_id=request_id,
    )
    return JSONResponse(
        status_code=exc.status_code,
        content=_error_payload(
            exc.code,
            exc.message,
            details=exc.details,
            request_id=request_id,
        ),
    )


async def validation_error_handler(
    request: Request,
    exc: RequestValidationError,
) -> JSONResponse:
    request_id: str | None = getattr(request.state, "request_id", None)
    details = [
        {
            "field": ".".join(str(loc) for loc in error["loc"]),
            "message": error["msg"],
        }
        for error in exc.errors()
    ]
    logger.warning(
        "validation_error",
        error_count=len(details),
        request_id=request_id,
    )
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=_error_payload(
            ErrorCode.VALIDATION_ERROR,
            "Request validation failed",
            details=details,
            request_id=request_id,
        ),
    )


async def pydantic_validation_error_handler(
    request: Request,
    exc: ValidationError,
) -> JSONResponse:
    request_id: str | None = getattr(request.state, "request_id", None)
    details = [
        {
            "field": ".".join(str(loc) for loc in error["loc"]),
            "message": error["msg"],
        }
        for error in exc.errors()
    ]
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=_error_payload(
            ErrorCode.VALIDATION_ERROR,
            "Data validation failed",
            details=details,
            request_id=request_id,
        ),
    )


async def http_exception_handler(
    request: Request,
    exc: StarletteHTTPException,
) -> JSONResponse:
    request_id: str | None = getattr(request.state, "request_id", None)
    code_map: dict[int, ErrorCode] = {
        401: ErrorCode.UNAUTHORIZED,
        403: ErrorCode.FORBIDDEN,
        404: ErrorCode.NOT_FOUND,
        409: ErrorCode.CONFLICT,
        503: ErrorCode.SERVICE_UNAVAILABLE,
    }
    code = code_map.get(exc.status_code, ErrorCode.INTERNAL_ERROR)
    message = exc.detail if isinstance(exc.detail, str) else "An error occurred"
    return JSONResponse(
        status_code=exc.status_code,
        content=_error_payload(code, message, request_id=request_id),
    )


async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    request_id: str | None = getattr(request.state, "request_id", None)
    logger.exception(
        "unhandled_exception",
        request_id=request_id,
        exc_type=type(exc).__name__,
    )
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=_error_payload(
            ErrorCode.INTERNAL_ERROR,
            "An unexpected error occurred",
            request_id=request_id,
        ),
    )


def register_exception_handlers(app: FastAPI) -> None:
    app.add_exception_handler(AppError, cast(Any, app_error_handler))
    app.add_exception_handler(RequestValidationError, cast(Any, validation_error_handler))
    app.add_exception_handler(ValidationError, cast(Any, pydantic_validation_error_handler))
    app.add_exception_handler(StarletteHTTPException, cast(Any, http_exception_handler))
    app.add_exception_handler(Exception, unhandled_exception_handler)
