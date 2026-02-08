"""Data access helpers for payment persistence."""

from __future__ import annotations

from typing import Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from shared.models.db import Payment as PaymentORM
from shared.models.payment import PaymentRequest, PaymentResponse


async def save_payment(
    session: AsyncSession,
    *,
    payment: PaymentResponse,
    request: PaymentRequest,
    provider: str,
    fraud_risk_score: Optional[float] = None,
    fraud_reason: Optional[str] = None,
) -> PaymentORM:
    """Persist payment response into PostgreSQL."""
    db_obj = await session.get(PaymentORM, payment.payment_id)
    if not db_obj:
        db_obj = PaymentORM(payment_id=payment.payment_id)
        session.add(db_obj)

    db_obj.merchant_id = payment.merchant_id
    db_obj.amount = payment.amount
    db_obj.currency = payment.currency
    db_obj.status = payment.status.value
    db_obj.payment_method = payment.payment_method.value
    db_obj.description = request.description
    db_obj.customer_email = request.customer_email
    db_obj.requires_action = payment.requires_action
    db_obj.next_action = payment.next_action
    db_obj.next_action_url = payment.next_action_url
    db_obj.error_message = payment.error_message
    db_obj.metadata_json = payment.metadata
    db_obj.transaction_id = payment.transaction_id
    db_obj.provider = provider
    db_obj.fraud_risk_score = fraud_risk_score
    db_obj.fraud_reason = fraud_reason

    await session.flush()
    return db_obj


async def get_payment(session: AsyncSession, payment_id: UUID) -> Optional[PaymentORM]:
    """Return payment by ID."""
    return await session.get(PaymentORM, payment_id)


async def list_payments_for_merchant(
    session: AsyncSession,
    merchant_id: UUID,
) -> list[PaymentORM]:
    """Return payments filtered by merchant (helper for future expansions)."""
    result = await session.execute(
        select(PaymentORM)
        .where(PaymentORM.merchant_id == merchant_id)
        .order_by(PaymentORM.created_at.desc())
    )
    return list(result.scalars())


async def list_all_payments(
    session: AsyncSession,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
) -> list[PaymentORM]:
    """Return all payments, optionally filtered by date range."""
    from datetime import datetime

    query = select(PaymentORM)

    if date_from:
        try:
            date_from_obj = datetime.fromisoformat(date_from.replace("Z", "+00:00"))
            query = query.where(PaymentORM.created_at >= date_from_obj)
        except (ValueError, AttributeError):
            pass

    if date_to:
        try:
            date_to_obj = datetime.fromisoformat(date_to.replace("Z", "+00:00"))
            # Add one day to include the entire end date
            from datetime import timedelta

            date_to_obj = date_to_obj + timedelta(days=1)
            query = query.where(PaymentORM.created_at < date_to_obj)
        except (ValueError, AttributeError):
            pass

    query = query.order_by(PaymentORM.created_at.desc())
    result = await session.execute(query)
    return list(result.scalars())
