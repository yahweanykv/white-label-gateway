"""Unit tests for gateway payments helper functions."""

from datetime import datetime
from decimal import Decimal
from uuid import uuid4

import pytest
from gateway.api.payments import _build_mock_query, _enrich_with_next_action

from shared.models.merchant import Merchant, MerchantStatus
from shared.models.payment import PaymentMethod, PaymentResponse, PaymentStatus


@pytest.fixture
def mock_merchant():
    """Create mock merchant."""
    return Merchant(
        merchant_id=uuid4(),
        name="Test Merchant",
        email="test@example.com",
        status=MerchantStatus.ACTIVE,
        api_key="sk_test_123",
        logo_url="https://example.com/logo.png",
        primary_color="#FF0000",
        background_color="#FFFFFF",
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )


def test_build_mock_query(mock_merchant):
    """Test _build_mock_query helper function."""
    payment = PaymentResponse(
        payment_id=uuid4(),
        merchant_id=mock_merchant.merchant_id,
        amount=Decimal("100.00"),
        currency="USD",
        status=PaymentStatus.SUCCEEDED,
        payment_method=PaymentMethod.CARD,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )

    query = _build_mock_query(payment, mock_merchant)
    assert "paymentId" in query
    assert "merchantName" in query
    assert "amount" in query
    assert "currency" in query
    assert str(payment.payment_id) in query


def test_build_mock_query_with_defaults():
    """Test _build_mock_query with default merchant values."""
    merchant = Merchant(
        merchant_id=uuid4(),
        name="Default Merchant",
        email="default@example.com",
        status=MerchantStatus.ACTIVE,
        api_key="sk_test",
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
        logo_url=None,
        primary_color=None,
        background_color=None,
    )

    payment = PaymentResponse(
        payment_id=uuid4(),
        merchant_id=merchant.merchant_id,
        amount=Decimal("50.00"),
        currency="EUR",
        status=PaymentStatus.SUCCEEDED,
        payment_method=PaymentMethod.CARD,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )

    query = _build_mock_query(payment, merchant)
    assert "DEFAULT_LOGO" in query or "via.placeholder.com" in query


def test_enrich_with_next_action_3ds(mock_merchant):
    """Test _enrich_with_next_action with 3DS action."""
    payment = PaymentResponse(
        payment_id=uuid4(),
        merchant_id=mock_merchant.merchant_id,
        amount=Decimal("100.00"),
        currency="USD",
        status=PaymentStatus.REQUIRES_ACTION,
        payment_method=PaymentMethod.CARD,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
        requires_action=True,
        next_action={"type": "redirect", "path": "/mock-3ds"},
    )

    enriched = _enrich_with_next_action(payment, mock_merchant)
    assert enriched.next_action_url is not None
    assert "/mock-3ds" in enriched.next_action_url
    assert "url" in enriched.next_action
    assert enriched.next_action["url"] == enriched.next_action_url


def test_enrich_with_next_action_no_action(mock_merchant):
    """Test _enrich_with_next_action when no action required."""
    payment = PaymentResponse(
        payment_id=uuid4(),
        merchant_id=mock_merchant.merchant_id,
        amount=Decimal("100.00"),
        currency="USD",
        status=PaymentStatus.SUCCEEDED,
        payment_method=PaymentMethod.CARD,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
        requires_action=False,
    )

    enriched = _enrich_with_next_action(payment, mock_merchant)
    assert enriched == payment


def test_enrich_with_next_action_other_action_type(mock_merchant):
    """Test _enrich_with_next_action with other action type."""
    payment = PaymentResponse(
        payment_id=uuid4(),
        merchant_id=mock_merchant.merchant_id,
        amount=Decimal("100.00"),
        currency="USD",
        status=PaymentStatus.REQUIRES_ACTION,
        payment_method=PaymentMethod.CARD,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
        requires_action=True,
        next_action={"type": "other", "path": "/other"},
    )

    enriched = _enrich_with_next_action(payment, mock_merchant)
    # Should not modify payment for non-redirect actions
    assert enriched.next_action_url is None or enriched.next_action_url == payment.next_action_url


def test_enrich_with_next_action_no_next_action(mock_merchant):
    """Test _enrich_with_next_action when next_action is None."""
    payment = PaymentResponse(
        payment_id=uuid4(),
        merchant_id=mock_merchant.merchant_id,
        amount=Decimal("100.00"),
        currency="USD",
        status=PaymentStatus.REQUIRES_ACTION,
        payment_method=PaymentMethod.CARD,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
        requires_action=True,
        next_action=None,
    )

    enriched = _enrich_with_next_action(payment, mock_merchant)
    assert enriched == payment
