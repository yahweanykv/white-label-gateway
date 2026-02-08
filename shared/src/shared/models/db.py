"""Shared SQLAlchemy ORM models."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Any, Optional
from uuid import UUID, uuid4

from sqlalchemy import Boolean, DateTime, Integer, Numeric, String
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from shared.database import Base


class Merchant(Base):
    """Merchant database model shared across services."""

    __tablename__ = "merchants"

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    domain: Mapped[Optional[str]] = mapped_column(String(255), nullable=True, unique=True, index=True)
    logo_url: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    primary_color: Mapped[Optional[str]] = mapped_column(String(7), nullable=True)
    background_color: Mapped[Optional[str]] = mapped_column(String(7), nullable=True)
    api_keys: Mapped[list[str]] = mapped_column(ARRAY(String), nullable=False)
    webhook_url: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=datetime.utcnow
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )

    def __repr__(self) -> str:  # pragma: no cover - debug helper
        return f"<Merchant(id={self.id}, name={self.name}, domain={self.domain})>"


class Payment(Base):
    """Payment record stored in payment_db."""

    __tablename__ = "payments"

    payment_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )
    merchant_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False, index=True)
    amount: Mapped[Decimal] = mapped_column(Numeric(precision=12, scale=2), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    payment_method: Mapped[str] = mapped_column(String(32), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    customer_email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    requires_action: Mapped[bool] = mapped_column(Boolean, default=False)
    next_action: Mapped[Optional[dict[str, Any]]] = mapped_column(JSONB, nullable=True)
    next_action_url: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    error_message: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    metadata_json: Mapped[Optional[dict[str, Any]]] = mapped_column(
        "metadata", JSONB, nullable=True
    )
    transaction_id: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    provider: Mapped[str] = mapped_column(String(64), nullable=False, default="mock")
    fraud_risk_score: Mapped[Optional[Decimal]] = mapped_column(Numeric(precision=5, scale=2), nullable=True)
    fraud_reason: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=datetime.utcnow, index=True
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )


class GatewayPaymentLog(Base):
    """Audit log for gateway payment requests stored in merchant_db."""

    __tablename__ = "gateway_payment_logs"

    request_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )
    merchant_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False, index=True)
    payment_id: Mapped[Optional[UUID]] = mapped_column(PGUUID(as_uuid=True), nullable=True, index=True)
    path: Mapped[str] = mapped_column(String(255), nullable=False)
    method: Mapped[str] = mapped_column(String(16), nullable=False)
    status_code: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    request_payload: Mapped[Optional[dict[str, Any]]] = mapped_column(JSONB, nullable=True)
    response_payload: Mapped[Optional[dict[str, Any]]] = mapped_column(JSONB, nullable=True)
    metadata_json: Mapped[Optional[dict[str, Any]]] = mapped_column("metadata", JSONB, nullable=True)
    error_message: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.utcnow,
        index=True,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )

    def mark_response(
        self,
        *,
        status_code: Optional[int],
        response_payload: Optional[dict[str, Any]],
        error_message: Optional[str] = None,
        payment_id: Optional[UUID] = None,
    ) -> None:
        """Update audit entry with response metadata."""
        self.status_code = status_code
        self.response_payload = response_payload
        self.error_message = error_message
        if payment_id:
            self.payment_id = payment_id

__all__ = ["Merchant", "Payment", "GatewayPaymentLog"]

