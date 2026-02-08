"""Payment API routes."""

import time
from datetime import datetime
from typing import Annotated, Optional
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from payment_service.config import settings
from payment_service.core.mock_providers import get_provider, payment_store
from payment_service.api.providers import get_current_provider_name
from payment_service.deps import get_db, verify_merchant_api_key
from payment_service.integrations import (
    notify_customer,
    perform_fraud_check,
    publish_payment_event,
)
from payment_service.repository import (
    get_payment,
    list_payments_for_merchant,
    list_all_payments,
    save_payment,
)
from shared.models.payment import (
    PaymentRequest,
    PaymentResponse,
    PaymentStatus,
)
from shared.metrics import (
    payments_total,
    payment_amount_total,
    payment_processing_duration_seconds,
    three_ds_attempts_total,
)

router = APIRouter()


def _should_use_mock_provider() -> bool:
    return settings.environment.lower() == "local" and "mock" in settings.payment_provider.lower()


async def _process_real_payment(
    payment_request: PaymentRequest,
) -> PaymentResponse:  # pragma: no cover - placeholder for future
    """Placeholder for future real provider integration."""
    now = datetime.utcnow()
    payment = PaymentResponse(
        payment_id=uuid4(),
        merchant_id=payment_request.merchant_id,
        amount=payment_request.amount,
        currency=payment_request.currency,
        status=PaymentStatus.PROCESSING,
        payment_method=payment_request.payment_method,
        created_at=now,
        updated_at=now,
        transaction_id=f"txn_{uuid4().hex[:8]}",
        metadata={"provider": "yc_secret_placeholder"},
    )
    await payment_store.save(payment)
    return payment


@router.post("/", response_model=PaymentResponse, status_code=status.HTTP_201_CREATED)
async def create_payment(
    payment_request: PaymentRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    verified_merchant_id: Annotated[UUID, Depends(verify_merchant_api_key)],
):
    """
    Create a new payment.

    Args:
        payment_request: Payment request data
        db: Database session
        verified_merchant_id: Verified merchant ID from API key

    Returns:
        Created payment response
    """
    # Verify that merchant_id in request matches the API key
    if payment_request.merchant_id != verified_merchant_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Merchant ID in request does not match API key",
        )

    start_time = time.time()

    fraud_result = await perform_fraud_check(payment_request)

    if fraud_result and fraud_result.get("is_fraud"):
        now = datetime.utcnow()
        payment = PaymentResponse(
            payment_id=uuid4(),
            merchant_id=payment_request.merchant_id,
            amount=payment_request.amount,
            currency=payment_request.currency,
            status=PaymentStatus.FAILED,
            payment_method=payment_request.payment_method,
            created_at=now,
            updated_at=now,
            error_message=fraud_result.get("reason", "Fraud check failed"),
            metadata={"fraud_risk_score": fraud_result.get("risk_score")},
        )
    elif _should_use_mock_provider():
        current_provider = get_current_provider_name()
        provider = get_provider(current_provider)
        payment = await provider.process(payment_request)
    else:
        payment = await _process_real_payment(payment_request)

    await save_payment(
        db,
        payment=payment,
        request=payment_request,
        provider=settings.payment_provider,
        fraud_risk_score=fraud_result.get("risk_score") if fraud_result else None,
        fraud_reason=fraud_result.get("reason") if fraud_result else None,
    )

    # Record metrics
    duration = time.time() - start_time
    payments_total.labels(
        status=payment.status.value,
        payment_method=payment.payment_method.value,
        currency=payment.currency,
        service="payment-service",
    ).inc()

    payment_amount_total.labels(
        currency=payment.currency,
        service="payment-service",
    ).inc(float(payment.amount))

    payment_processing_duration_seconds.labels(
        status=payment.status.value,
        service="payment-service",
    ).observe(duration)

    if payment.status == PaymentStatus.REQUIRES_ACTION:
        three_ds_attempts_total.labels(
            status="initiated",
            service="payment-service",
        ).inc()

    await notify_customer(payment, payment_request.customer_email)
    await publish_payment_event(
        payment,
        customer_email=payment_request.customer_email,
        metadata=payment_request.metadata,
    )

    return payment


@router.get("/all", response_model=list[PaymentResponse])
async def get_all_payments(
    db: Annotated[AsyncSession, Depends(get_db)],
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
):
    """
    Get all payments, optionally filtered by date range.

    For demo purposes only - in production this should require authentication.

    Args:
        db: Database session
        date_from: Start date (YYYY-MM-DD)
        date_to: End date (YYYY-MM-DD)

    Returns:
        List of payments
    """
    db_payments = await list_all_payments(db, date_from=date_from, date_to=date_to)
    payments = []
    for db_payment in db_payments:
        # Try to get from in-memory store first
        payment = await payment_store.get(db_payment.payment_id)
        if not payment:
            # Convert from DB model
            payment = PaymentResponse.model_validate(db_payment)
        payments.append(payment)
    return payments


@router.get("/by-merchant/{merchant_id}", response_model=list[PaymentResponse])
async def get_payments_by_merchant(
    merchant_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """
    Get all payments for a merchant.

    Args:
        merchant_id: Merchant ID
        db: Database session

    Returns:
        List of payments
    """
    db_payments = await list_payments_for_merchant(db, merchant_id)
    payments = []
    for db_payment in db_payments:
        # Try to get from in-memory store first
        payment = await payment_store.get(db_payment.payment_id)
        if not payment:
            # Convert from DB model
            payment = PaymentResponse.model_validate(db_payment)
        payments.append(payment)
    return payments


@router.get("/{payment_id}", response_model=PaymentResponse)
async def get_payment_endpoint(
    payment_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    verified_merchant_id: Annotated[UUID, Depends(verify_merchant_api_key)],
):
    """
    Get payment by ID.

    Args:
        payment_id: Payment ID
        db: Database session
        verified_merchant_id: Verified merchant ID from API key

    Returns:
        Payment response
    """
    payment = await payment_store.get(payment_id)
    if not payment:
        db_payment = await get_payment(db, payment_id)
        if db_payment:
            payment = PaymentResponse.model_validate(db_payment)
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Payment not found",
            )

    # Verify that payment belongs to the authenticated merchant
    if payment.merchant_id != verified_merchant_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Payment does not belong to this merchant",
        )

    return payment


@router.post("/{payment_id}/complete-3ds", response_model=PaymentResponse)
async def complete_three_ds(
    payment_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """
    Complete 3DS authentication and mark the payment as succeeded.

    Args:
        payment_id: Payment identifier

    Returns:
        Updated payment response
    """
    payment = await payment_store.update(
        payment_id,
        status=PaymentStatus.SUCCEEDED,
        requires_action=False,
        next_action=None,
        next_action_url=None,
    )
    if not payment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Payment not found",
        )

    # Record 3DS completion metric
    three_ds_attempts_total.labels(
        status="completed",
        service="payment-service",
    ).inc()

    # Update payment metrics
    payments_total.labels(
        status=PaymentStatus.SUCCEEDED.value,
        payment_method=payment.payment_method.value,
        currency=payment.currency,
        service="payment-service",
    ).inc()

    db_payment = await get_payment(db, payment_id)
    if db_payment:
        db_payment.status = PaymentStatus.SUCCEEDED.value
        db_payment.requires_action = False
        db_payment.next_action = None
        db_payment.next_action_url = None

    await notify_customer(payment, db_payment.customer_email if db_payment else None)
    await publish_payment_event(
        payment,
        customer_email=db_payment.customer_email if db_payment else None,
        metadata=(db_payment.metadata_json if db_payment else {}) or {},
    )

    return payment
