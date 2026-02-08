"""Models for notification service."""

from datetime import datetime
from enum import Enum
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


class DeliveryStatus(str, Enum):
    """Delivery status enumeration."""

    PENDING = "pending"
    SUCCESS = "success"
    FAILED = "failed"
    RETRYING = "retrying"


class NotificationType(str, Enum):
    """Notification type enumeration."""

    EMAIL = "email"
    WEBHOOK = "webhook"


class PaymentEvent(BaseModel):
    """Payment event from RabbitMQ."""

    event_type: str = Field(..., description="Event type: payment.succeeded or payment.failed")
    payment_id: UUID = Field(..., description="Payment ID")
    merchant_id: UUID = Field(..., description="Merchant ID")
    amount: str = Field(..., description="Payment amount")
    currency: str = Field(..., description="Payment currency")
    status: str = Field(..., description="Payment status")
    customer_email: Optional[str] = Field(None, description="Customer email")
    metadata: Optional[dict] = Field(None, description="Additional metadata")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Event timestamp")


class DeliveryAttempt(BaseModel):
    """Delivery attempt log."""

    attempt_number: int = Field(..., ge=1, description="Attempt number")
    notification_type: NotificationType = Field(..., description="Notification type")
    status: DeliveryStatus = Field(..., description="Delivery status")
    error_message: Optional[str] = Field(None, description="Error message if failed")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Attempt timestamp")
    response_code: Optional[int] = Field(None, description="HTTP response code for webhooks")
    response_body: Optional[str] = Field(None, description="Response body for webhooks")

