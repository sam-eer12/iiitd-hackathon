"""Public error envelopes and domain exceptions."""

from typing import Any

from fastapi import HTTPException, Request, status
from fastapi.responses import JSONResponse


class AppError(Exception):
    def __init__(
        self,
        code: str,
        message: str,
        status_code: int = status.HTTP_400_BAD_REQUEST,
        retryable: bool = False,
        details: dict[str, Any] | None = None,
    ):
        super().__init__(message)
        self.code = code
        self.message = message
        self.status_code = status_code
        self.retryable = retryable
        self.details = details or {}


class AuthenticationError(AppError):
    def __init__(self, message: str = "Invalid or missing credentials"):
        super().__init__(
            code="AUTHENTICATION_FAILED",
            message=message,
            status_code=status.HTTP_401_UNAUTHORIZED,
        )


class ForbiddenError(AppError):
    def __init__(self, message: str = "You do not have access to this resource"):
        super().__init__(
            code="FORBIDDEN",
            message=message,
            status_code=status.HTTP_403_FORBIDDEN,
        )


class NotFoundError(AppError):
    def __init__(self, message: str = "Resource not found"):
        super().__init__(
            code="NOT_FOUND",
            message=message,
            status_code=status.HTTP_404_NOT_FOUND,
        )


class ConflictError(AppError):
    def __init__(self, code: str = "CONFLICT", message: str = "Conflict occurred"):
        super().__init__(
            code=code,
            message=message,
            status_code=status.HTTP_409_CONFLICT,
        )


class ProfileVersionConflictError(ConflictError):
    def __init__(self, message: str = "Your supplier profile changed. Reload it before saving."):
        super().__init__(
            code="PROFILE_VERSION_CONFLICT",
            message=message,
        )


class IdempotencyConflictError(ConflictError):
    def __init__(self, message: str = "Reusing idempotency key with different payload."):
        super().__init__(
            code="IDEMPOTENCY_CONFLICT",
            message=message,
        )


class PayloadTooLargeError(AppError):
    def __init__(self, message: str = "Document or payload exceeds maximum allowed size"):
        super().__init__(
            code="PAYLOAD_TOO_LARGE",
            message=message,
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
        )


class UnprocessableFactError(AppError):
    def __init__(self, message: str = "Invalid or unprocessable facts provided"):
        super().__init__(
            code="UNPROCESSABLE_FACTS",
            message=message,
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        )


class RateLimitExceededError(AppError):
    def __init__(self, message: str = "Cooldown in effect or rate limit exceeded"):
        super().__init__(
            code="RATE_LIMIT_EXCEEDED",
            message=message,
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            retryable=True,
        )


class ServiceUnavailableError(AppError):
    def __init__(self, message: str = "Required service is temporarily unavailable"):
        super().__init__(
            code="SERVICE_UNAVAILABLE",
            message=message,
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            retryable=True,
        )


def format_error_response(
    code: str,
    message: str,
    status_code: int,
    retryable: bool = False,
    request_id: str = "req_default",
) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content={
            "error": {
                "code": code,
                "message": message,
                "requestId": request_id,
                "retryable": retryable,
            }
        },
    )


async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
    request_id = getattr(request.state, "request_id", "req_unknown")
    return format_error_response(
        code=exc.code,
        message=exc.message,
        status_code=exc.status_code,
        retryable=exc.retryable,
        request_id=request_id,
    )


async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    request_id = getattr(request.state, "request_id", "req_unknown")
    code = "HTTP_ERROR"
    if exc.status_code == 401:
        code = "UNAUTHORIZED"
    elif exc.status_code == 403:
        code = "FORBIDDEN"
    elif exc.status_code == 404:
        code = "NOT_FOUND"
    elif exc.status_code == 409:
        code = "CONFLICT"
    elif exc.status_code == 422:
        code = "VALIDATION_ERROR"
    elif exc.status_code == 503:
        code = "SERVICE_UNAVAILABLE"

    return format_error_response(
        code=code,
        message=str(exc.detail),
        status_code=exc.status_code,
        request_id=request_id,
    )
