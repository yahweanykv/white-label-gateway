"""Unit tests for payment service routes."""

from datetime import datetime
from decimal import Decimal
from uuid import uuid4

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

import payment_service.api.payments as payments_module
from payment_service.api.payments import router
from payment_service.deps import get_db
from shared.models.payment import PaymentMethod, PaymentRequest, PaymentStatus


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

    async def fake_save_payment(*args, **kwargs):
        return None

    async def fake_get_payment(*args, **kwargs):
        # Return None to force lookup from payment_store
        return None

    async def fake_notify_customer(*args, **kwargs):
        return None

    async def fake_publish_event(*args, **kwargs):
        return None

    async def fake_fraud_check(*args, **kwargs):
        return {"is_fraud": False, "risk_score": 0.1}

    original_dep = payments_module.get_db
    original_save = payments_module.save_payment
    original_get = payments_module.get_payment
    original_notify = payments_module.notify_customer
    original_publish = payments_module.publish_payment_event
    original_fraud = payments_module.perform_fraud_check
    original_settings = payments_module.settings

    payments_module.get_db = override_get_db
    payments_module.save_payment = fake_save_payment
    payments_module.get_payment = fake_get_payment
    payments_module.notify_customer = fake_notify_customer
    payments_module.publish_payment_event = fake_publish_event
    payments_module.perform_fraud_check = fake_fraud_check

    try:
        yield app
    finally:
        app.dependency_overrides.pop(get_db, None)
        payments_module.get_db = original_dep
        payments_module.save_payment = original_save
        payments_module.get_payment = original_get
        payments_module.notify_customer = original_notify
        payments_module.publish_payment_event = original_publish
        payments_module.perform_fraud_check = original_fraud
        payments_module.settings = original_settings


@pytest.fixture
def client(app):
    """Create test client."""
    assert get_db in app.dependency_overrides
    return TestClient(app)


class TestPaymentServiceRoutes:
    """Tests for payment service routes."""

    def test_create_payment_success(self, client, monkeypatch):
        """Test successful payment creation with mock_success provider."""
        monkeypatch.setenv("ENVIRONMENT", "local")
        monkeypatch.setenv("PAYMENT_PROVIDER", "mock_success")
        # Override settings to ensure mock provider is used
        import payment_service.api.payments as payments_module

        payments_module.settings.environment = "local"
        payments_module.settings.payment_provider = "mock_success"

        merchant_id = uuid4()
        payment_request = {
            "merchant_id": str(merchant_id),
            "amount": "100.00",
            "currency": "USD",
            "payment_method": "card",
        }

        response = client.post("/api/v1/payments", json=payment_request)
        assert response.status_code == 201
        data = response.json()
        assert data["status"] == "succeeded"
        assert data["amount"] == "100.00"
        assert data["currency"] == "USD"
        assert "payment_id" in data
        assert "transaction_id" in data

    def test_create_payment_failed(self, client, monkeypatch):
        """Test failed payment creation with mock_failed provider."""
        monkeypatch.setenv("ENVIRONMENT", "local")
        monkeypatch.setenv("PAYMENT_PROVIDER", "mock_failed")
        # Override settings to ensure mock provider is used
        import payment_service.api.payments as payments_module

        payments_module.settings.environment = "local"
        payments_module.settings.payment_provider = "mock_failed"

        merchant_id = uuid4()
        payment_request = {
            "merchant_id": str(merchant_id),
            "amount": "50.00",
            "currency": "EUR",
            "payment_method": "card",
        }

        response = client.post("/api/v1/payments", json=payment_request)
        assert response.status_code == 201
        data = response.json()
        assert data["status"] == "failed"
        assert "error_message" in data

    def test_create_payment_3ds(self, client, monkeypatch):
        """Test 3DS payment creation with mock_3ds provider."""
        monkeypatch.setenv("ENVIRONMENT", "local")
        monkeypatch.setenv("PAYMENT_PROVIDER", "mock_3ds")
        # Override settings to ensure mock provider is used
        import payment_service.api.payments as payments_module

        payments_module.settings.environment = "local"
        payments_module.settings.payment_provider = "mock_3ds"

        merchant_id = uuid4()
        payment_request = {
            "merchant_id": str(merchant_id),
            "amount": "150.00",
            "currency": "RUB",
            "payment_method": "card",
        }

        response = client.post("/api/v1/payments", json=payment_request)
        assert response.status_code == 201
        data = response.json()
        assert data["status"] == "requires_action"
        assert data["requires_action"] is True
        assert "next_action" in data
        assert data["next_action"]["type"] == "redirect"

    def test_get_payment_success(self, client, monkeypatch):
        """Test getting payment after creation."""
        monkeypatch.setenv("ENVIRONMENT", "local")
        monkeypatch.setenv("PAYMENT_PROVIDER", "mock_success")
        # Override settings to ensure mock provider is used
        import payment_service.api.payments as payments_module

        payments_module.settings.environment = "local"
        payments_module.settings.payment_provider = "mock_success"

        merchant_id = uuid4()
        payment_request = {
            "merchant_id": str(merchant_id),
            "amount": "200.00",
            "currency": "USD",
            "payment_method": "card",
        }

        create_response = client.post("/api/v1/payments", json=payment_request)
        assert create_response.status_code == 201
        payment_id = create_response.json()["payment_id"]

        get_response = client.get(f"/api/v1/payments/{payment_id}")
        assert get_response.status_code == 200
        data = get_response.json()
        assert data["payment_id"] == payment_id
        assert data["status"] == "succeeded"

    def test_get_payment_not_found(self, client):
        """Test getting non-existent payment."""
        payment_id = uuid4()
        response = client.get(f"/api/v1/payments/{payment_id}")
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    def test_complete_3ds_success(self, client, monkeypatch):
        """Test completing 3DS payment."""
        monkeypatch.setenv("ENVIRONMENT", "local")
        monkeypatch.setenv("PAYMENT_PROVIDER", "mock_3ds")
        # Override settings to ensure mock provider is used
        import payment_service.api.payments as payments_module

        payments_module.settings.environment = "local"
        payments_module.settings.payment_provider = "mock_3ds"

        merchant_id = uuid4()
        payment_request = {
            "merchant_id": str(merchant_id),
            "amount": "300.00",
            "currency": "GBP",
            "payment_method": "card",
        }

        create_response = client.post("/api/v1/payments", json=payment_request)
        assert create_response.status_code == 201
        payment_id = create_response.json()["payment_id"]
        assert create_response.json()["status"] == "requires_action"

        complete_response = client.post(f"/api/v1/payments/{payment_id}/complete-3ds")
        assert complete_response.status_code == 200
        data = complete_response.json()
        assert data["status"] == "succeeded"
        assert data["requires_action"] is False
        assert data["next_action"] is None

    def test_complete_3ds_not_found(self, client):
        """Test completing non-existent 3DS payment."""
        payment_id = uuid4()
        response = client.post(f"/api/v1/payments/{payment_id}/complete-3ds")
        assert response.status_code == 404

    def test_create_payment_merchant_id_mismatch(self, client, monkeypatch):
        """Test payment creation with merchant ID mismatch."""
        monkeypatch.setenv("ENVIRONMENT", "local")
        monkeypatch.setenv("PAYMENT_PROVIDER", "mock_success")
        import payment_service.api.payments as payments_module

        payments_module.settings.environment = "local"
        payments_module.settings.payment_provider = "mock_success"

        merchant_id = uuid4()
        different_merchant_id = uuid4()
        payment_request = {
            "merchant_id": str(different_merchant_id),
            "amount": "100.00",
            "currency": "USD",
            "payment_method": "card",
        }

        # Mock verify_merchant_api_key to return merchant_id
        from payment_service.deps import verify_merchant_api_key

        original_verify = verify_merchant_api_key

        async def mock_verify():
            return merchant_id

        import payment_service.api.payments as pm

        pm.verify_merchant_api_key = mock_verify

        try:
            response = client.post(
                "/api/v1/payments", json=payment_request, headers={"X-API-Key": "sk_test"}
            )
            assert response.status_code == 403
            assert "does not match" in response.json()["detail"].lower()
        finally:
            pm.verify_merchant_api_key = original_verify

    def test_get_all_payments(self, client, monkeypatch):
        """Test getting all payments."""
        from datetime import datetime
        from payment_service.repository import list_all_payments
        from shared.models.payment import PaymentORM

        async def mock_list_all_payments(session, date_from=None, date_to=None):
            return []

        import payment_service.api.payments as pm

        original_list = pm.list_all_payments
        pm.list_all_payments = mock_list_all_payments

        try:
            response = client.get("/api/v1/payments/all")
            assert response.status_code == 200
            assert isinstance(response.json(), list)
        finally:
            pm.list_all_payments = original_list

    def test_get_all_payments_with_date_filter(self, client, monkeypatch):
        """Test getting all payments with date filter."""

        async def mock_list_all_payments(session, date_from=None, date_to=None):
            return []

        import payment_service.api.payments as pm

        original_list = pm.list_all_payments
        pm.list_all_payments = mock_list_all_payments

        try:
            response = client.get("/api/v1/payments/all?date_from=2024-01-01&date_to=2024-01-31")
            assert response.status_code == 200
            assert isinstance(response.json(), list)
        finally:
            pm.list_all_payments = original_list

    def test_get_payments_by_merchant(self, client, monkeypatch):
        """Test getting payments by merchant."""
        from payment_service.repository import list_payments_for_merchant

        async def mock_list_payments_for_merchant(session, merchant_id):
            return []

        import payment_service.api.payments as pm

        original_list = pm.list_payments_for_merchant
        pm.list_payments_for_merchant = mock_list_payments_for_merchant

        try:
            merchant_id = uuid4()
            response = client.get(f"/api/v1/payments/by-merchant/{merchant_id}")
            assert response.status_code == 200
            assert isinstance(response.json(), list)
        finally:
            pm.list_payments_for_merchant = original_list

    def test_get_payment_from_db(self, client, monkeypatch):
        """Test getting payment from database when not in store."""
        from datetime import datetime
        from payment_service.repository import get_payment
        from shared.models.payment import PaymentORM
        from shared.models.db import Payment as PaymentDB

        payment_id = uuid4()
        merchant_id = uuid4()

        async def mock_get_payment(session, p_id):
            if p_id == payment_id:
                db_payment = PaymentDB()
                db_payment.payment_id = payment_id
                db_payment.merchant_id = merchant_id
                db_payment.amount = Decimal("100.00")
                db_payment.currency = "USD"
                db_payment.status = "succeeded"
                db_payment.payment_method = "card"
                db_payment.created_at = datetime.utcnow()
                db_payment.updated_at = datetime.utcnow()
                return db_payment
            return None

        import payment_service.api.payments as pm
        from payment_service.deps import verify_merchant_api_key

        original_get = pm.get_payment
        pm.get_payment = mock_get_payment

        async def mock_verify():
            return merchant_id

        original_verify = verify_merchant_api_key
        pm.verify_merchant_api_key = mock_verify

        try:
            response = client.get(
                f"/api/v1/payments/{payment_id}", headers={"X-API-Key": "sk_test"}
            )
            assert response.status_code == 200
            assert response.json()["payment_id"] == str(payment_id)
        finally:
            pm.get_payment = original_get
            pm.verify_merchant_api_key = original_verify

    def test_get_payment_wrong_merchant(self, client, monkeypatch):
        """Test getting payment that belongs to different merchant."""
        from datetime import datetime
        from payment_service.core.mock_providers import payment_store
        from shared.models.payment import PaymentResponse, PaymentStatus, PaymentMethod

        payment_id = uuid4()
        merchant_id = uuid4()
        different_merchant_id = uuid4()

        # Create payment in store with one merchant
        payment = PaymentResponse(
            payment_id=payment_id,
            merchant_id=merchant_id,
            amount=Decimal("100.00"),
            currency="USD",
            status=PaymentStatus.SUCCEEDED,
            payment_method=PaymentMethod.CARD,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        payment_store._store[payment_id] = payment

        import payment_service.api.payments as pm
        from payment_service.deps import verify_merchant_api_key

        async def mock_verify():
            return different_merchant_id

        original_verify = verify_merchant_api_key
        pm.verify_merchant_api_key = mock_verify

        try:
            response = client.get(
                f"/api/v1/payments/{payment_id}", headers={"X-API-Key": "sk_test"}
            )
            assert response.status_code == 403
            assert "does not belong" in response.json()["detail"].lower()
        finally:
            pm.verify_merchant_api_key = original_verify
            payment_store._store.pop(payment_id, None)
