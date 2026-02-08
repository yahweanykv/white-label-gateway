"""Pydantic schemas for merchant service."""

from datetime import datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, Field, HttpUrl


class MerchantBase(BaseModel):
    """Base merchant schema."""

    name: str = Field(..., min_length=1, max_length=255, description="Merchant name")
    domain: Optional[str] = Field(None, max_length=255, description="Merchant domain")
    logo_url: Optional[HttpUrl] = Field(None, description="Merchant logo URL")
    primary_color: Optional[str] = Field(
        None, pattern="^#[0-9A-Fa-f]{6}$", description="Primary brand color in hex format"
    )
    background_color: Optional[str] = Field(
        None, pattern="^#[0-9A-Fa-f]{6}$", description="Background color in hex format"
    )
    webhook_url: Optional[HttpUrl] = Field(None, description="Webhook URL for notifications")


class MerchantCreate(MerchantBase):
    """Merchant creation schema."""

    logo_url: Optional[str] = Field(None, description="Merchant logo URL (can be HTTP URL or base64 data URL)")


class MerchantUpdate(BaseModel):
    """Merchant update schema."""

    name: Optional[str] = Field(None, min_length=1, max_length=255)
    domain: Optional[str] = Field(None, max_length=255)
    logo_url: Optional[str] = Field(None, description="Merchant logo URL (can be HTTP URL or base64 data URL)")
    primary_color: Optional[str] = Field(None, pattern="^#[0-9A-Fa-f]{6}$")
    background_color: Optional[str] = Field(None, pattern="^#[0-9A-Fa-f]{6}$")
    webhook_url: Optional[HttpUrl] = None


class MerchantResponse(MerchantBase):
    """Merchant response schema."""

    id: UUID
    api_keys: List[str] = Field(..., description="List of API keys")
    is_active: bool
    created_at: datetime
    updated_at: datetime
    logo_url: Optional[str] = Field(None, description="Merchant logo URL (can be HTTP URL or base64 data URL)")

    class Config:
        """Pydantic config."""

        from_attributes = True


class MerchantByApiKeyResponse(BaseModel):
    """Merchant response for API key lookup."""

    merchant_id: UUID
    name: str
    email: str
    status: str
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

