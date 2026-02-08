"""Unit tests for mock payment providers."""

from decimal import Decimal
from uuid import uuid4

import pytest

from payment_service.core.mock_providers import (
    FailedMockProvider,
    PaymentStore,
    RandomMockProvider,
    SlowMockProvider,
    SuccessMockProvider,
    ThreeDSMockProvider,
    get_provider,
)
from shared.models.payment import PaymentMethod, PaymentRequest, PaymentStatus


class TestPaymentStore:
    """Tests for PaymentStore."""

    @pytest.mark.asyncio
    async def test_save_and_get_payment(self):
        """Test saving and retrieving payment."""
        store = PaymentStore()
        merchant_id = uuid4()
        payment_request = PaymentRequest(
            merchant_id=merchant_id,
            amount=Decimal("100.00"),
            currency="USD",
            payment_method=PaymentMethod.CARD,
        )
        provider = SuccessMockProvider(store)
        payment = await provider.process(payment_request)

        retrieved = await store.get(payment.payment_id)
        assert retrieved is not None
        assert retrieved.payment_id == payment.payment_id
        assert retrieved.amount == Decimal("100.00")

    @pytest.mark.asyncio
    async def test_get_nonexistent_payment(self):
        """Test getting non-existent payment."""
        store = PaymentStore()
        result = await store.get(uuid4())
        assert result is None

    @pytest.mark.asyncio
    async def test_update_payment(self):
        """Test updating payment status."""
        store = PaymentStore()
        merchant_id = uuid4()
        payment_request = PaymentRequest(
            merchant_id=merchant_id,
            amount=Decimal("50.00"),
            currency="EUR",
            payment_method=PaymentMethod.CARD,
        )
        provider = SuccessMockProvider(store)
        payment = await provider.process(payment_request)

        updated = await store.update(
            payment.payment_id,
            status=PaymentStatus.FAILED,
            error_message="Test error",
        )
        assert updated is not None
        assert updated.status == PaymentStatus.FAILED
        assert updated.error_message == "Test error"


class TestSuccessMockProvider:
    """Tests for SuccessMockProvider."""

    @pytest.mark.asyncio
    async def test_process_success(self):
        """Test successful payment processing."""
        store = PaymentStore()
        provider = SuccessMockProvider(store)
        merchant_id = uuid4()
        payment_request = PaymentRequest(
            merchant_id=merchant_id,
            amount=Decimal("100.00"),
            currency="USD",
            payment_method=PaymentMethod.CARD,
        )

        payment = await provider.process(payment_request)

        assert payment.status == PaymentStatus.SUCCEEDED
        assert payment.transaction_id is not None
        assert payment.transaction_id.startswith("txn_")
        assert payment.error_message is None


class TestFailedMockProvider:
    """Tests for FailedMockProvider."""

    @pytest.mark.asyncio
    async def test_process_failure(self):
        """Test failed payment processing."""
        store = PaymentStore()
        provider = FailedMockProvider(store)
        merchant_id = uuid4()
        payment_request = PaymentRequest(
            merchant_id=merchant_id,
            amount=Decimal("200.00"),
            currency="EUR",
            payment_method=PaymentMethod.CARD,
        )

        payment = await provider.process(payment_request)

        assert payment.status == PaymentStatus.FAILED
        assert payment.error_message == "Mocked decline: insufficient funds"
        assert payment.transaction_id is None


class TestThreeDSMockProvider:
    """Tests for ThreeDSMockProvider."""

    @pytest.mark.asyncio
    async def test_process_3ds(self):
        """Test 3DS payment processing."""
        store = PaymentStore()
        provider = ThreeDSMockProvider(store)
        merchant_id = uuid4()
        payment_request = PaymentRequest(
            merchant_id=merchant_id,
            amount=Decimal("150.00"),
            currency="RUB",
            payment_method=PaymentMethod.CARD,
        )

        payment = await provider.process(payment_request)

        assert payment.status == PaymentStatus.REQUIRES_ACTION
        assert payment.requires_action is True
        assert payment.next_action is not None
        assert payment.next_action["type"] == "redirect"
        assert payment.next_action["path"] == "/mock-3ds"
        assert payment.next_action["payment_id"] == str(payment.payment_id)


class TestSlowMockProvider:
    """Tests for SlowMockProvider."""

    @pytest.mark.asyncio
    async def test_process_slow(self):
        """Test slow payment processing."""
        store = PaymentStore()
        provider = SlowMockProvider(store)
        merchant_id = uuid4()
        payment_request = PaymentRequest(
            merchant_id=merchant_id,
            amount=Decimal("75.00"),
            currency="GBP",
            payment_method=PaymentMethod.CARD,
        )

        payment = await provider.process(payment_request)

        assert payment.status == PaymentStatus.PROCESSING
        assert payment.metadata is not None
        assert "expected_settlement_seconds" in payment.metadata


class TestRandomMockProvider:
    """Tests for RandomMockProvider."""

    @pytest.mark.asyncio
    async def test_process_random(self):
        """Test random payment processing."""
        store = PaymentStore()
        base_providers = {
            "mock_success": SuccessMockProvider(store),
            "mock_failed": FailedMockProvider(store),
            "mock_3ds": ThreeDSMockProvider(store),
        }
        provider = RandomMockProvider(store, base_providers)
        merchant_id = uuid4()
        payment_request = PaymentRequest(
            merchant_id=merchant_id,
            amount=Decimal("300.00"),
            currency="USD",
            payment_method=PaymentMethod.CARD,
        )

        payment = await provider.process(payment_request)

        # Should return one of the base providers
        assert payment.status in [
            PaymentStatus.SUCCEEDED,
            PaymentStatus.FAILED,
            PaymentStatus.REQUIRES_ACTION,
        ]


class TestGetProvider:
    """Tests for get_provider function."""

    def test_get_success_provider(self):
        """Test getting success provider."""
        provider = get_provider("mock_success")
        assert isinstance(provider, SuccessMockProvider)

    def test_get_failed_provider(self):
        """Test getting failed provider."""
        provider = get_provider("mock_failed")
        assert isinstance(provider, FailedMockProvider)

    def test_get_3ds_provider(self):
        """Test getting 3DS provider."""
        provider = get_provider("mock_3ds")
        assert isinstance(provider, ThreeDSMockProvider)

    def test_get_unknown_provider_defaults_to_success(self):
        """Test getting unknown provider defaults to success."""
        provider = get_provider("unknown_provider")
        assert isinstance(provider, SuccessMockProvider)

    def test_get_provider_case_insensitive(self):
        """Test provider name is case insensitive."""
        provider1 = get_provider("MOCK_SUCCESS")
        provider2 = get_provider("mock_success")
        assert type(provider1) == type(provider2)
