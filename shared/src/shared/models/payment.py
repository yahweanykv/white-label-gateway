"""Payment-related models."""

from decimal import Decimal
from enum import Enum
from typing import Optional
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class PaymentStatus(str, Enum):
    """Payment status enumeration."""

    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    CANCELLED = "cancelled"
    REFUNDED = "refunded"
    REQUIRES_ACTION = "requires_action"


class PaymentMethod(str, Enum):
    """Payment method enumeration."""

    CARD = "card"
    BANK_TRANSFER = "bank_transfer"
    DIGITAL_WALLET = "digital_wallet"


class PaymentRequest(BaseModel):
    """Payment request model."""

    merchant_id: UUID
    amount: Decimal = Field(..., gt=0, decimal_places=2)
    currency: str = Field(..., min_length=3, max_length=3)
    payment_method: PaymentMethod
    description: Optional[str] = None
    customer_email: Optional[str] = None
    metadata: Optional[dict] = None


class PaymentResponse(BaseModel):
    """Payment response model."""

    payment_id: UUID
    merchant_id: UUID
    amount: Decimal
    currency: str
    status: PaymentStatus
    payment_method: PaymentMethod
    created_at: datetime
    updated_at: datetime
    transaction_id: Optional[str] = None
    error_message: Optional[str] = None
    requires_action: bool = False
    next_action: Optional[dict] = None
    next_action_url: Optional[str] = None
    metadata: Optional[dict] = Field(default=None, alias="metadata_json")

    class Config:
        """Pydantic config."""

        from_attributes = True
        populate_by_name = True
