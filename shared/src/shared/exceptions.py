"""Custom HTTP exceptions with error codes."""

from typing import Any, Optional

from fastapi import HTTPException, status


class BaseAPIException(HTTPException):
    """Base API exception with error code."""

    def __init__(
        self,
        status_code: int,
        error_code: str,
        detail: Any = None,
        headers: Optional[dict[str, Any]] = None,
    ):
        """
        Initialize API exception.

        Args:
            status_code: HTTP status code
            error_code: Application error code
            detail: Error detail message
            headers: Optional HTTP headers
        """
        super().__init__(status_code=status_code, detail=detail, headers=headers)
        self.error_code = error_code


# Authentication & Authorization
class UnauthorizedError(BaseAPIException):
    """401 Unauthorized error."""

    def __init__(self, detail: str = "Authentication required"):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            error_code="UNAUTHORIZED",
            detail=detail,
        )


class ForbiddenError(BaseAPIException):
    """403 Forbidden error."""

    def __init__(self, detail: str = "Access forbidden"):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            error_code="FORBIDDEN",
            detail=detail,
        )


# Validation errors
class ValidationError(BaseAPIException):
    """400 Bad Request - Validation error."""

    def __init__(self, detail: str = "Validation failed", field: Optional[str] = None):
        error_detail = detail
        if field:
            error_detail = f"{field}: {detail}"
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            error_code="VALIDATION_ERROR",
            detail=error_detail,
        )


class NotFoundError(BaseAPIException):
    """404 Not Found error."""

    def __init__(self, resource: str = "Resource", resource_id: Optional[str] = None):
        detail = f"{resource} not found"
        if resource_id:
            detail = f"{resource} with id {resource_id} not found"
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            error_code="NOT_FOUND",
            detail=detail,
        )


# Business logic errors
class ConflictError(BaseAPIException):
    """409 Conflict error."""

    def __init__(self, detail: str = "Resource conflict"):
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            error_code="CONFLICT",
            detail=detail,
        )


class PaymentError(BaseAPIException):
    """400 Bad Request - Payment processing error."""

    def __init__(self, detail: str = "Payment processing failed"):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            error_code="PAYMENT_ERROR",
            detail=detail,
        )


class InsufficientFundsError(BaseAPIException):
    """402 Payment Required - Insufficient funds."""

    def __init__(self, detail: str = "Insufficient funds"):
        super().__init__(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            error_code="INSUFFICIENT_FUNDS",
            detail=detail,
        )


class FraudDetectionError(BaseAPIException):
    """403 Forbidden - Fraud detected."""

    def __init__(self, detail: str = "Transaction flagged as fraudulent"):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            error_code="FRAUD_DETECTED",
            detail=detail,
        )


# External service errors
class ExternalServiceError(BaseAPIException):
    """502 Bad Gateway - External service error."""

    def __init__(self, service: str, detail: str = "External service unavailable"):
        super().__init__(
            status_code=status.HTTP_502_BAD_GATEWAY,
            error_code="EXTERNAL_SERVICE_ERROR",
            detail=f"{service}: {detail}",
        )


class ServiceUnavailableError(BaseAPIException):
    """503 Service Unavailable error."""

    def __init__(self, detail: str = "Service temporarily unavailable"):
        super().__init__(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            error_code="SERVICE_UNAVAILABLE",
            detail=detail,
        )


# Rate limiting
class RateLimitError(BaseAPIException):
    """429 Too Many Requests error."""

    def __init__(self, detail: str = "Rate limit exceeded", retry_after: Optional[int] = None):
        headers = None
        if retry_after:
            headers = {"Retry-After": str(retry_after)}
        super().__init__(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            error_code="RATE_LIMIT_EXCEEDED",
            detail=detail,
            headers=headers,
        )
