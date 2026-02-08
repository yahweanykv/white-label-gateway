"""Common response schemas."""

from typing import Any, Generic, Optional, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class SuccessResponse(BaseModel, Generic[T]):
    """Standard success response schema."""

    success: bool = Field(default=True, description="Operation success status")
    data: T = Field(..., description="Response data")
    message: Optional[str] = Field(default=None, description="Optional success message")

    class Config:
        """Pydantic config."""

        json_schema_extra = {
            "example": {
                "success": True,
                "data": {"id": "123", "name": "Example"},
                "message": "Operation completed successfully",
            }
        }


class ErrorDetail(BaseModel):
    """Error detail schema."""

    field: Optional[str] = Field(default=None, description="Field name if validation error")
    message: str = Field(..., description="Error message")
    code: Optional[str] = Field(default=None, description="Error code")

    class Config:
        """Pydantic config."""

        json_schema_extra = {
            "example": {
                "field": "email",
                "message": "Invalid email format",
                "code": "INVALID_EMAIL",
            }
        }


class ErrorResponse(BaseModel):
    """Standard error response schema."""

    success: bool = Field(default=False, description="Operation success status")
    error: str = Field(..., description="Error message")
    error_code: Optional[str] = Field(default=None, description="Error code")
    details: Optional[list[ErrorDetail]] = Field(
        default=None, description="Detailed error information"
    )
    request_id: Optional[str] = Field(default=None, description="Request ID for tracing")

    class Config:
        """Pydantic config."""

        json_schema_extra = {
            "example": {
                "success": False,
                "error": "Validation failed",
                "error_code": "VALIDATION_ERROR",
                "details": [
                    {
                        "field": "email",
                        "message": "Invalid email format",
                        "code": "INVALID_EMAIL",
                    }
                ],
                "request_id": "req-123456",
            }
        }


class HealthCheckResponse(BaseModel):
    """Health check response schema."""

    status: str = Field(..., description="Service status")
    version: Optional[str] = Field(default=None, description="Service version")
    checks: Optional[dict[str, bool]] = Field(default=None, description="Individual service checks")

    class Config:
        """Pydantic config."""

        json_schema_extra = {
            "example": {
                "status": "healthy",
                "version": "0.1.0",
                "checks": {
                    "database": True,
                    "redis": True,
                },
            }
        }


class MessageResponse(BaseModel):
    """Simple message response schema."""

    message: str = Field(..., description="Response message")

    class Config:
        """Pydantic config."""

        json_schema_extra = {
            "example": {
                "message": "Operation completed successfully",
            }
        }
