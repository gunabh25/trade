from enum import StrEnum
from typing import Any


class ErrorCode(StrEnum):
    VALIDATION_ERROR = "VALIDATION_ERROR"
    NOT_FOUND = "NOT_FOUND"
    UNAUTHORIZED = "UNAUTHORIZED"
    FORBIDDEN = "FORBIDDEN"
    CONFLICT = "CONFLICT"
    RATE_LIMIT_EXCEEDED = "RATE_LIMIT_EXCEEDED"
    INTERNAL_ERROR = "INTERNAL_ERROR"
    SERVICE_UNAVAILABLE = "SERVICE_UNAVAILABLE"


class AppError(Exception):
    """Base application exception with HTTP mapping."""

    def __init__(
        self,
        code: ErrorCode,
        message: str,
        *,
        status_code: int = 400,
        details: list[dict[str, Any]] | None = None,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.status_code = status_code
        self.details = details or []


class NotFoundError(AppError):
    def __init__(self, message: str = "Resource not found") -> None:
        super().__init__(ErrorCode.NOT_FOUND, message, status_code=404)


class UnauthorizedError(AppError):
    def __init__(self, message: str = "Authentication required") -> None:
        super().__init__(ErrorCode.UNAUTHORIZED, message, status_code=401)


class ForbiddenError(AppError):
    def __init__(self, message: str = "Access denied") -> None:
        super().__init__(ErrorCode.FORBIDDEN, message, status_code=403)


class ConflictError(AppError):
    def __init__(self, message: str = "Resource conflict") -> None:
        super().__init__(ErrorCode.CONFLICT, message, status_code=409)


class ValidationError(AppError):
    def __init__(self, message: str = "Invalid request") -> None:
        super().__init__(ErrorCode.VALIDATION_ERROR, message, status_code=400)


class RateLimitError(AppError):
    def __init__(
        self,
        message: str = "Too many AI requests. Please slow down.",
        *,
        retry_after: int = 60,
    ) -> None:
        super().__init__(
            ErrorCode.RATE_LIMIT_EXCEEDED,
            message,
            status_code=429,
            details=[{"retryAfterSeconds": retry_after}],
        )


class ServiceUnavailableError(AppError):
    def __init__(self, message: str = "Service temporarily unavailable") -> None:
        super().__init__(ErrorCode.SERVICE_UNAVAILABLE, message, status_code=503)
