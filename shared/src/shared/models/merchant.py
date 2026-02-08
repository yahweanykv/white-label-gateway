"""Merchant-related models."""

from datetime import datetime
from enum import Enum
from uuid import UUID
from typing import Optional

from pydantic import BaseModel, EmailStr, Field


class MerchantStatus(str, Enum):
    """Merchant status enumeration."""

    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"
    PENDING_VERIFICATION = "pending_verification"


class Merchant(BaseModel):
    """Merchant model."""

    merchant_id: UUID
    name: str = Field(..., min_length=1, max_length=255)
    email: EmailStr
    status: MerchantStatus
    api_key: str
    logo_url: Optional[str] = None
    primary_color: Optional[str] = None
    background_color: Optional[str] = None
    webhook_url: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    metadata: Optional[dict] = None

    class Config:
        """Pydantic config."""

        from_attributes = True


class MerchantCreate(BaseModel):
    """Merchant creation model."""

    name: str = Field(..., min_length=1, max_length=255)
    email: EmailStr
    webhook_url: Optional[str] = None
    metadata: Optional[dict] = None

