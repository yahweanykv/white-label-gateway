"""Unit tests for shared models."""

from datetime import datetime
from decimal import Decimal
from uuid import uuid4

import pytest
from pydantic import ValidationError

from shared.models.merchant import Merchant, MerchantCreate, MerchantStatus
from shared.models.payment import (
    PaymentMethod,
    PaymentRequest,
    PaymentResponse,
    PaymentStatus,
)


class TestMerchantModels:
    """Tests for merchant models."""

    def test_merchant_create_valid(self):
        """Test creating valid merchant."""
        merchant = MerchantCreate(
            name="Test Merchant",
            email="test@example.com",
            webhook_url="https://example.com/webhook",
        )
        assert merchant.name == "Test Merchant"
        assert merchant.email == "test@example.com"
        assert merchant.webhook_url == "https://example.com/webhook"

    def test_merchant_create_minimal(self):
        """Test creating merchant with minimal fields."""
        merchant = MerchantCreate(name="Minimal", email="min@example.com")
        assert merchant.name == "Minimal"
        assert merchant.email == "min@example.com"
        assert merchant.webhook_url is None

    def test_merchant_create_invalid_email(self):
        """Test creating merchant with invalid email."""
        with pytest.raises(ValidationError):
            MerchantCreate(name="Test", email="invalid-email")

    def test_merchant_create_empty_name(self):
        """Test creating merchant with empty name."""
        with pytest.raises(ValidationError):
            MerchantCreate(name="", email="test@example.com")

    def test_merchant_create_long_name(self):
        """Test creating merchant with too long name."""
        long_name = "a" * 256
        with pytest.raises(ValidationError):
            MerchantCreate(name=long_name, email="test@example.com")

    def test_merchant_full_model(self):
        """Test full merchant model."""
        merchant_id = uuid4()
        now = datetime.utcnow()
        merchant = Merchant(
            merchant_id=merchant_id,
            name="Full Merchant",
            email="full@example.com",
            status=MerchantStatus.ACTIVE,
            api_key="sk_test_123",
            logo_url="https://example.com/logo.png",
            primary_color="#FF0000",
            background_color="#FFFFFF",
            webhook_url="https://example.com/webhook",
            created_at=now,
            updated_at=now,
            metadata={"key": "value"},
        )
        assert merchant.merchant_id == merchant_id
        assert merchant.status == MerchantStatus.ACTIVE
        assert merchant.metadata == {"key": "value"}

    def test_merchant_status_enum(self):
        """Test merchant status enum values."""
        assert MerchantStatus.ACTIVE == "active"
        assert MerchantStatus.INACTIVE == "inactive"
        assert MerchantStatus.SUSPENDED == "suspended"
        assert MerchantStatus.PENDING_VERIFICATION == "pending_verification"


class TestPaymentModels:
    """Tests for payment models."""

    def test_payment_request_valid(self):
        """Test creating valid payment request."""
        merchant_id = uuid4()
        payment = PaymentRequest(
            merchant_id=merchant_id,
            amount=Decimal("100.50"),
            currency="USD",
            payment_method=PaymentMethod.CARD,
            description="Test payment",
            customer_email="customer@example.com",
        )
        assert payment.merchant_id == merchant_id
        assert payment.amount == Decimal("100.50")
        assert payment.currency == "USD"
        assert payment.payment_method == PaymentMethod.CARD

    def test_payment_request_minimal(self):
        """Test creating payment request with minimal fields."""
        merchant_id = uuid4()
        payment = PaymentRequest(
            merchant_id=merchant_id,
            amount=Decimal("50.00"),
            currency="EUR",
            payment_method=PaymentMethod.CARD,
        )
        assert payment.amount == Decimal("50.00")
        assert payment.description is None

    def test_payment_request_invalid_amount_zero(self):
        """Test creating payment request with zero amount."""
        with pytest.raises(ValidationError):
            PaymentRequest(
                merchant_id=uuid4(),
                amount=Decimal("0.00"),
                currency="USD",
                payment_method=PaymentMethod.CARD,
            )

    def test_payment_request_invalid_amount_negative(self):
        """Test creating payment request with negative amount."""
        with pytest.raises(ValidationError):
            PaymentRequest(
                merchant_id=uuid4(),
                amount=Decimal("-10.00"),
                currency="USD",
                payment_method=PaymentMethod.CARD,
            )

    def test_payment_request_invalid_currency_length(self):
        """Test creating payment request with invalid currency length."""
        with pytest.raises(ValidationError):
            PaymentRequest(
                merchant_id=uuid4(),
                amount=Decimal("100.00"),
                currency="US",
                payment_method=PaymentMethod.CARD,
            )

    def test_payment_request_decimal_places(self):
        """Test payment amount with correct decimal places."""
        merchant_id = uuid4()
        payment = PaymentRequest(
            merchant_id=merchant_id,
            amount=Decimal("99.99"),
            currency="RUB",
            payment_method=PaymentMethod.CARD,
        )
        assert payment.amount == Decimal("99.99")

    def test_payment_response_full(self):
        """Test full payment response model."""
        payment_id = uuid4()
        merchant_id = uuid4()
        now = datetime.utcnow()
        payment = PaymentResponse(
            payment_id=payment_id,
            merchant_id=merchant_id,
            amount=Decimal("200.00"),
            currency="USD",
            status=PaymentStatus.SUCCEEDED,
            payment_method=PaymentMethod.CARD,
            created_at=now,
            updated_at=now,
            transaction_id="txn_12345",
            requires_action=False,
            metadata={"provider": "mock"},
        )
        assert payment.payment_id == payment_id
        assert payment.status == PaymentStatus.SUCCEEDED
        assert payment.transaction_id == "txn_12345"

    def test_payment_status_enum(self):
        """Test payment status enum values."""
        assert PaymentStatus.PENDING == "pending"
        assert PaymentStatus.PROCESSING == "processing"
        assert PaymentStatus.COMPLETED == "completed"
        assert PaymentStatus.SUCCEEDED == "succeeded"
        assert PaymentStatus.FAILED == "failed"
        assert PaymentStatus.REQUIRES_ACTION == "requires_action"

    def test_payment_method_enum(self):
        """Test payment method enum values."""
        assert PaymentMethod.CARD == "card"
        assert PaymentMethod.BANK_TRANSFER == "bank_transfer"
        assert PaymentMethod.DIGITAL_WALLET == "digital_wallet"

    def test_payment_response_with_3ds(self):
        """Test payment response with 3DS action."""
        payment_id = uuid4()
        merchant_id = uuid4()
        now = datetime.utcnow()
        payment = PaymentResponse(
            payment_id=payment_id,
            merchant_id=merchant_id,
            amount=Decimal("150.00"),
            currency="EUR",
            status=PaymentStatus.REQUIRES_ACTION,
            payment_method=PaymentMethod.CARD,
            created_at=now,
            updated_at=now,
            requires_action=True,
            next_action={"type": "redirect", "path": "/mock-3ds"},
            next_action_url="/mock-3ds?paymentId=123",
        )
        assert payment.requires_action is True
        assert payment.next_action == {"type": "redirect", "path": "/mock-3ds"}
