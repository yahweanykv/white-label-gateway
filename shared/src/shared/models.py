"""Base Pydantic models for type safety."""

from decimal import Decimal
from typing import Annotated
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


# Type aliases for better type safety
TenantUUID = Annotated[UUID, Field(description="Tenant identifier")]
MerchantId = Annotated[UUID, Field(description="Merchant identifier")]
PaymentId = Annotated[UUID, Field(description="Payment identifier")]
TransactionId = Annotated[str, Field(description="Transaction identifier", min_length=1)]


class Amount(BaseModel):
    """Amount with currency validation."""

    value: Decimal = Field(..., gt=0, decimal_places=2, description="Amount value")
    currency: str = Field(
        ...,
        min_length=3,
        max_length=3,
        description="ISO 4217 currency code (e.g., USD, EUR, RUB)",
    )

    @field_validator("currency")
    @classmethod
    def validate_currency(cls, v: str) -> str:
        """Validate currency code is uppercase."""
        return v.upper()

    @field_validator("value")
    @classmethod
    def validate_value(cls, v: Decimal) -> Decimal:
        """Validate amount precision."""
        if v.as_tuple().exponent < -2:
            raise ValueError("Amount cannot have more than 2 decimal places")
        return v

    class Config:
        """Pydantic config."""

        json_schema_extra = {
            "example": {
                "value": "100.50",
                "currency": "USD",
            }
        }


class TimestampMixin(BaseModel):
    """Mixin for models with timestamps."""

    created_at: Annotated[
        str,
        Field(
            description="ISO 8601 timestamp of creation",
            examples=["2024-01-01T00:00:00Z"],
        ),
    ]
    updated_at: Annotated[
        str,
        Field(
            description="ISO 8601 timestamp of last update",
            examples=["2024-01-01T00:00:00Z"],
        ),
    ]


class TenantMixin(BaseModel):
    """Mixin for models with tenant isolation."""

    tenant_id: TenantUUID = Field(..., description="Tenant identifier for multi-tenancy")


class PaginationParams(BaseModel):
    """Pagination parameters."""

    page: int = Field(default=1, ge=1, description="Page number (1-based)")
    page_size: int = Field(default=20, ge=1, le=100, description="Items per page")

    @property
    def offset(self) -> int:
        """Calculate offset for database queries."""
        return (self.page - 1) * self.page_size

    @property
    def limit(self) -> int:
        """Get limit for database queries."""
        return self.page_size


class PaginatedResponse(BaseModel):
    """Paginated response wrapper."""

    total: int = Field(..., ge=0, description="Total number of items")
    page: int = Field(..., ge=1, description="Current page number")
    page_size: int = Field(..., ge=1, description="Items per page")
    total_pages: int = Field(..., ge=0, description="Total number of pages")

    @classmethod
    def create(cls, total: int, page: int, page_size: int) -> "PaginatedResponse":
        """Create paginated response with calculated total_pages."""
        total_pages = (total + page_size - 1) // page_size if total > 0 else 0
        return cls(
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        )

