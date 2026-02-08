"""Extended unit tests for payment service payments routes."""

from datetime import datetime
from decimal import Decimal
from unittest.mock import MagicMock
from uuid import uuid4

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from payment_service.api.payments import router
from payment_service.deps import get_db

from shared.models.payment import PaymentStatus


@pytest.fixture
def app():
    """Create test FastAPI app with dependency overrides."""
    app = FastAPI()
    app.include_router(router, prefix="/api/v1/payments")

    class DummySession:
        async def get(self, *_, **__):
            return None

        async def flush(self):
            return None

        def add(self, _obj):
            return None

    async def override_get_db():
        yield DummySession()

    app.dependency_overrides[get_db] = override_get_db

    import payment_service.api.payments as payments_module

    original_save = payments_module.save_payment
    original_get = payments_module.get_payment
    original_list = payments_module.list_payments_for_merchant
    original_notify = payments_module.notify_customer
    original_publish = payments_module.publish_payment_event
    original_fraud = payments_module.perform_fraud_check
    original_settings = payments_module.settings

    async def fake_save_payment(*args, **kwargs):
        return None

    async def fake_get_payment(*args, **kwargs):
        return None

    async def fake_list_payments(*args, **kwargs):
        return []

    async def fake_notify_customer(*args, **kwargs):
        return None

    async def fake_publish_event(*args, **kwargs):
        return None

    async def fake_fraud_check(*args, **kwargs):
        return {"is_fraud": False, "risk_score": 0.1}

    payments_module.save_payment = fake_save_payment
    payments_module.get_payment = fake_get_payment
    payments_module.list_payments_for_merchant = fake_list_payments
    payments_module.notify_customer = fake_notify_customer
    payments_module.publish_payment_event = fake_publish_event
    payments_module.perform_fraud_check = fake_fraud_check
    payments_module.settings.environment = "local"
    payments_module.settings.payment_provider = "mock_success"

    try:
        yield app
    finally:
        app.dependency_overrides.pop(get_db, None)
        payments_module.save_payment = original_save
        payments_module.get_payment = original_get
        payments_module.list_payments_for_merchant = original_list
        payments_module.notify_customer = original_notify
        payments_module.publish_payment_event = original_publish
        payments_module.perform_fraud_check = original_fraud
        payments_module.settings = original_settings


@pytest.fixture
def client(app):
    """Create test client."""
    return TestClient(app)


class TestPaymentServicePaymentsExtended:
    """Extended tests for payment service routes."""

    def test_create_payment_with_fraud_detected(self, client, monkeypatch):
        """Test payment creation with fraud detected."""
        import payment_service.api.payments as payments_module

        payments_module.settings.environment = "local"
        payments_module.settings.payment_provider = "mock_success"

        async def fake_fraud_check(*args, **kwargs):
            return {"is_fraud": True, "risk_score": 0.9, "reason": "High risk transaction"}

        payments_module.perform_fraud_check = fake_fraud_check

        merchant_id = uuid4()
        payment_request = {
            "merchant_id": str(merchant_id),
            "amount": "1000.00",
            "currency": "USD",
            "payment_method": "card",
        }

        response = client.post("/api/v1/payments", json=payment_request)
        assert response.status_code == 201
        data = response.json()
        assert data["status"] == "failed"
        assert "error_message" in data
        assert "fraud" in data["error_message"].lower() or "risk" in data["error_message"].lower()

    def test_get_payments_by_merchant(self, client, monkeypatch):
        """Test getting payments by merchant ID."""
        import payment_service.api.payments as payments_module

        payments_module.settings.environment = "local"
        payments_module.settings.payment_provider = "mock_success"

        merchant_id = uuid4()
        response = client.get(f"/api/v1/payments/by-merchant/{merchant_id}")
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    def test_get_payment_from_db(self, client, monkeypatch):
        """Test getting payment from database when not in store."""
        from datetime import datetime

        import payment_service.api.payments as payments_module

        from shared.models.db import Payment as PaymentORM

        payment_id = uuid4()
        merchant_id = uuid4()

        # Mock get_payment to return a DB payment
        db_payment = MagicMock(spec=PaymentORM)
        db_payment.payment_id = payment_id
        db_payment.merchant_id = merchant_id
        db_payment.amount = Decimal("100.00")
        db_payment.currency = "USD"
        db_payment.status = "succeeded"
        db_payment.payment_method = "card"
        db_payment.created_at = datetime.utcnow()
        db_payment.updated_at = datetime.utcnow()
        db_payment.requires_action = False
        db_payment.next_action = None
        db_payment.next_action_url = None
        db_payment.transaction_id = "txn_test"
        db_payment.error_message = None
        db_payment.metadata_json = None

        async def fake_get_payment(*args, **kwargs):
            return db_payment

        payments_module.get_payment = fake_get_payment

        response = client.get(f"/api/v1/payments/{payment_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["payment_id"] == str(payment_id)

    def test_complete_3ds_with_db_payment(self, client, monkeypatch):
        """Test completing 3DS payment with DB payment."""
        import payment_service.api.payments as payments_module
        from payment_service.core.mock_providers import payment_store

        from shared.models.db import Payment as PaymentORM
        from shared.models.payment import PaymentMethod, PaymentResponse

        payments_module.settings.environment = "local"
        payments_module.settings.payment_provider = "mock_3ds"

        merchant_id = uuid4()
        payment_id = uuid4()

        # Create payment in store
        payment = PaymentResponse(
            payment_id=payment_id,
            merchant_id=merchant_id,
            amount=Decimal("100.00"),
            currency="USD",
            status=PaymentStatus.REQUIRES_ACTION,
            payment_method=PaymentMethod.CARD,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            requires_action=True,
            next_action={"type": "redirect", "path": "/mock-3ds"},
        )
        payment_store._payments[payment_id] = payment

        # Mock get_payment to return a DB payment
        db_payment = MagicMock(spec=PaymentORM)
        db_payment.payment_id = payment_id
        db_payment.customer_email = "test@example.com"
        db_payment.metadata_json = {}

        async def fake_get_payment(*args, **kwargs):
            return db_payment

        payments_module.get_payment = fake_get_payment

        response = client.post(f"/api/v1/payments/{payment_id}/complete-3ds")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "succeeded"
        assert data["requires_action"] is False
