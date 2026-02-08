"""Unit tests for payment service repository."""

from datetime import datetime
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest
from payment_service.repository import (
    get_payment,
    list_payments_for_merchant,
    save_payment,
)
from sqlalchemy.ext.asyncio import AsyncSession

from shared.models.db import Payment as PaymentORM
from shared.models.payment import PaymentMethod, PaymentRequest, PaymentResponse, PaymentStatus


@pytest.mark.asyncio
async def test_save_payment_new():
    """Test saving new payment."""
    session = AsyncMock(spec=AsyncSession)
    session.get = AsyncMock(return_value=None)
    session.add = MagicMock()
    session.flush = AsyncMock()

    payment = PaymentResponse(
        payment_id=uuid4(),
        merchant_id=uuid4(),
        amount=Decimal("100.00"),
        currency="USD",
        status=PaymentStatus.SUCCEEDED,
        payment_method=PaymentMethod.CARD,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )

    request = PaymentRequest(
        merchant_id=payment.merchant_id,
        amount=payment.amount,
        currency=payment.currency,
        payment_method=payment.payment_method,
    )

    result = await save_payment(
        session,
        payment=payment,
        request=request,
        provider="mock_success",
    )

    assert result is not None
    session.add.assert_called_once()
    session.flush.assert_called_once()


@pytest.mark.asyncio
async def test_save_payment_update():
    """Test updating existing payment."""
    payment_id = uuid4()
    existing_payment = MagicMock(spec=PaymentORM)
    existing_payment.payment_id = payment_id

    session = AsyncMock(spec=AsyncSession)
    session.get = AsyncMock(return_value=existing_payment)
    session.add = MagicMock()
    session.flush = AsyncMock()

    payment = PaymentResponse(
        payment_id=payment_id,
        merchant_id=uuid4(),
        amount=Decimal("200.00"),
        currency="EUR",
        status=PaymentStatus.SUCCEEDED,
        payment_method=PaymentMethod.CARD,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )

    request = PaymentRequest(
        merchant_id=payment.merchant_id,
        amount=payment.amount,
        currency=payment.currency,
        payment_method=payment.payment_method,
    )

    result = await save_payment(
        session,
        payment=payment,
        request=request,
        provider="mock_success",
    )

    assert result == existing_payment
    session.add.assert_not_called()
    session.flush.assert_called_once()


@pytest.mark.asyncio
async def test_get_payment_found():
    """Test getting payment that exists."""
    payment_id = uuid4()
    payment_orm = MagicMock(spec=PaymentORM)
    payment_orm.payment_id = payment_id

    session = AsyncMock(spec=AsyncSession)
    session.get = AsyncMock(return_value=payment_orm)

    result = await get_payment(session, payment_id)

    assert result == payment_orm
    session.get.assert_called_once_with(PaymentORM, payment_id)


@pytest.mark.asyncio
async def test_get_payment_not_found():
    """Test getting payment that doesn't exist."""
    payment_id = uuid4()

    session = AsyncMock(spec=AsyncSession)
    session.get = AsyncMock(return_value=None)

    result = await get_payment(session, payment_id)

    assert result is None


@pytest.mark.asyncio
async def test_list_payments_for_merchant():
    """Test listing payments for merchant."""

    merchant_id = uuid4()
    payment1 = MagicMock(spec=PaymentORM)
    payment2 = MagicMock(spec=PaymentORM)

    mock_result = MagicMock()
    mock_result.scalars.return_value = [payment1, payment2]
    session = AsyncMock(spec=AsyncSession)
    session.execute = AsyncMock(return_value=mock_result)

    result = await list_payments_for_merchant(session, merchant_id)

    assert len(result) == 2
    assert payment1 in result
    assert payment2 in result
    session.execute.assert_called_once()
