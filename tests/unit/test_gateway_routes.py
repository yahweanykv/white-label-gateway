"""Unit tests for gateway routes."""

from datetime import datetime
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest
from fastapi import HTTPException, status
from httpx import Response

from gateway.api.merchants import router as merchants_router
from gateway.api.payments import router as payments_router
from shared.models.merchant import Merchant, MerchantStatus
from shared.models.payment import PaymentMethod, PaymentRequest, PaymentResponse, PaymentStatus


class TestGatewayMerchantsRoutes:
    """Tests for gateway merchant routes."""

    @pytest.mark.asyncio
    @patch("gateway.api.merchants.httpx.AsyncClient")
    async def test_create_merchant_success(self, mock_client_class):
        """Test successful merchant creation."""
        from datetime import datetime
        
        merchant_id = uuid4()
        now = datetime.utcnow()
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "merchant_id": str(merchant_id),
            "name": "Test Merchant",
            "email": "test@example.com",
            "status": "active",
            "api_key": "sk_test_123",
            "created_at": now.isoformat(),
            "updated_at": now.isoformat(),
        }
        mock_response.status_code = 201
        mock_response.raise_for_status = MagicMock()

        mock_client = AsyncMock()
        mock_client.__aenter__.return_value = mock_client
        mock_client.__aexit__.return_value = None
        mock_client.post = AsyncMock(return_value=mock_response)
        mock_client_class.return_value = mock_client

        merchant_create = {
            "name": "Test Merchant",
            "email": "test@example.com",
        }

        # Create test app
        from fastapi import FastAPI
        from fastapi.testclient import TestClient

        app = FastAPI()
        app.include_router(merchants_router, prefix="/api/v1/merchants")
        client = TestClient(app)

        response = client.post("/api/v1/merchants", json=merchant_create)
        assert response.status_code == 201
        assert response.json()["name"] == "Test Merchant"

    @pytest.mark.asyncio
    @patch("gateway.api.merchants.httpx.AsyncClient")
    async def test_get_merchant_success(self, mock_client_class):
        """Test successful merchant retrieval."""
        from datetime import datetime
        
        merchant_id = uuid4()
        now = datetime.utcnow()
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "merchant_id": str(merchant_id),
            "name": "Test Merchant",
            "email": "test@example.com",
            "status": "active",
            "api_key": "sk_test_123",
            "created_at": now.isoformat(),
            "updated_at": now.isoformat(),
        }
        mock_response.status_code = 200
        mock_response.raise_for_status = MagicMock()

        mock_client = AsyncMock()
        mock_client.__aenter__.return_value = mock_client
        mock_client.__aexit__.return_value = None
        mock_client.get = AsyncMock(return_value=mock_response)
        mock_client_class.return_value = mock_client

        from fastapi import FastAPI
        from fastapi.testclient import TestClient

        app = FastAPI()
        app.include_router(merchants_router, prefix="/api/v1/merchants")
        client = TestClient(app)

        response = client.get(f"/api/v1/merchants/{merchant_id}")
        assert response.status_code == 200
        assert response.json()["merchant_id"] == str(merchant_id)

    @pytest.mark.asyncio
    @patch("gateway.api.merchants.httpx.AsyncClient")
    async def test_get_merchant_not_found(self, mock_client_class):
        """Test merchant not found."""
        from httpx import HTTPStatusError

        merchant_id = uuid4()
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_response.text = "Not found"

        mock_client = AsyncMock()
        mock_client.__aenter__.return_value = mock_client
        mock_client.__aexit__.return_value = None

        # Create HTTPStatusError for 404
        error = HTTPStatusError("Not found", request=MagicMock(), response=mock_response)
        mock_client.get = AsyncMock(side_effect=error)
        mock_client_class.return_value = mock_client

        from fastapi import FastAPI
        from fastapi.testclient import TestClient

        app = FastAPI()
        app.include_router(merchants_router, prefix="/api/v1/merchants")
        client = TestClient(app)

        response = client.get(f"/api/v1/merchants/{merchant_id}")
        assert response.status_code == 404


class TestGatewayPaymentsRoutes:
    """Tests for gateway payment routes."""

    @pytest.fixture
    def mock_merchant(self):
        """Create mock merchant."""
        now = datetime.utcnow()
        return Merchant(
            merchant_id=uuid4(),
            name="Test Merchant",
            email="test@example.com",
            status=MerchantStatus.ACTIVE,
            api_key="sk_test_123",
            logo_url="https://example.com/logo.png",
            primary_color="#FF0000",
            background_color="#FFFFFF",
            created_at=now,
            updated_at=now,
        )

    @pytest.mark.asyncio
    @patch("gateway.api.payments.httpx.AsyncClient")
    async def test_create_payment_success(self, mock_client_class, mock_merchant):
        """Test successful payment creation."""
        payment_id = uuid4()
        merchant_id = mock_merchant.merchant_id
        mock_response = MagicMock()
        from datetime import datetime
        now = datetime.utcnow()
        mock_response.json.return_value = {
            "payment_id": str(payment_id),
            "merchant_id": str(merchant_id),
            "amount": "100.00",
            "currency": "USD",
            "status": "succeeded",
            "payment_method": "card",
            "created_at": now.isoformat(),
            "updated_at": now.isoformat(),
            "requires_action": False,
            "transaction_id": "txn_test_123",
        }
        mock_response.status_code = 201
        mock_response.raise_for_status = MagicMock()

        mock_client = AsyncMock()
        mock_client.__aenter__.return_value = mock_client
        mock_client.__aexit__.return_value = None
        mock_client.post = AsyncMock(return_value=mock_response)
        mock_client_class.return_value = mock_client

        from fastapi import FastAPI, Depends
        from fastapi.testclient import TestClient

        async def get_current_merchant():
            return mock_merchant

        app = FastAPI()
        app.include_router(payments_router, prefix="/api/v1/payments", dependencies=[Depends(get_current_merchant)])
        client = TestClient(app)

        payment_request = {
            "merchant_id": str(merchant_id),
            "amount": "100.00",
            "currency": "USD",
            "payment_method": "card",
        }

        response = client.post("/api/v1/payments", json=payment_request)
        assert response.status_code == 201
        assert response.json()["payment_id"] == str(payment_id)

    @pytest.mark.asyncio
    @patch("gateway.api.payments.httpx.AsyncClient")
    async def test_create_payment_with_3ds(self, mock_client_class, mock_merchant):
        """Test payment creation with 3DS."""
        payment_id = uuid4()
        merchant_id = mock_merchant.merchant_id
        mock_response = MagicMock()
        from datetime import datetime
        now = datetime.utcnow()
        mock_response.json.return_value = {
            "payment_id": str(payment_id),
            "merchant_id": str(merchant_id),
            "amount": "150.00",
            "currency": "EUR",
            "status": "requires_action",
            "payment_method": "card",
            "created_at": now.isoformat(),
            "updated_at": now.isoformat(),
            "requires_action": True,
            "next_action": {"type": "redirect", "path": "/mock-3ds"},
            "transaction_id": "txn_test_456",
        }
        mock_response.status_code = 201
        mock_response.raise_for_status = MagicMock()

        mock_client = AsyncMock()
        mock_client.__aenter__.return_value = mock_client
        mock_client.__aexit__.return_value = None
        mock_client.post = AsyncMock(return_value=mock_response)
        mock_client_class.return_value = mock_client

        from fastapi import FastAPI, Depends
        from fastapi.testclient import TestClient

        async def get_current_merchant():
            return mock_merchant

        app = FastAPI()
        app.include_router(payments_router, prefix="/api/v1/payments", dependencies=[Depends(get_current_merchant)])
        client = TestClient(app)

        payment_request = {
            "merchant_id": str(merchant_id),
            "amount": "150.00",
            "currency": "EUR",
            "payment_method": "card",
        }

        response = client.post("/api/v1/payments", json=payment_request)
        assert response.status_code == 201
        assert response.json()["requires_action"] is True
        assert "next_action_url" in response.json()

    @pytest.mark.asyncio
    @patch("gateway.api.payments.httpx.AsyncClient")
    async def test_get_payment_success(self, mock_client_class, mock_merchant):
        """Test successful payment retrieval."""
        payment_id = uuid4()
        merchant_id = mock_merchant.merchant_id
        mock_response = MagicMock()
        from datetime import datetime
        now = datetime.utcnow()
        mock_response.json.return_value = {
            "payment_id": str(payment_id),
            "merchant_id": str(merchant_id),
            "amount": "200.00",
            "currency": "USD",
            "status": "succeeded",
            "payment_method": "card",
            "created_at": now.isoformat(),
            "updated_at": now.isoformat(),
            "requires_action": False,
            "transaction_id": "txn_test_789",
        }
        mock_response.status_code = 200
        mock_response.raise_for_status = MagicMock()

        mock_client = AsyncMock()
        mock_client.__aenter__.return_value = mock_client
        mock_client.__aexit__.return_value = None
        mock_client.get = AsyncMock(return_value=mock_response)
        mock_client_class.return_value = mock_client

        from fastapi import FastAPI, Depends
        from fastapi.testclient import TestClient

        async def get_current_merchant():
            return mock_merchant

        app = FastAPI()
        app.include_router(payments_router, prefix="/api/v1/payments", dependencies=[Depends(get_current_merchant)])
        client = TestClient(app)

        response = client.get(f"/api/v1/payments/{payment_id}")
        assert response.status_code == 200
        assert response.json()["payment_id"] == str(payment_id)

    @pytest.mark.asyncio
    @patch("gateway.api.payments.httpx.AsyncClient")
    async def test_get_payment_not_found(self, mock_client_class, mock_merchant):
        """Test payment not found."""
        from httpx import HTTPStatusError
        
        payment_id = uuid4()
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_response.text = "Not found"

        mock_client = AsyncMock()
        mock_client.__aenter__.return_value = mock_client
        mock_client.__aexit__.return_value = None
        error = HTTPStatusError("Not found", request=MagicMock(), response=mock_response)
        mock_client.get = AsyncMock(side_effect=error)
        mock_client_class.return_value = mock_client

        from fastapi import FastAPI, Depends
        from fastapi.testclient import TestClient

        async def get_current_merchant():
            return mock_merchant

        app = FastAPI()
        app.include_router(payments_router, prefix="/api/v1/payments", dependencies=[Depends(get_current_merchant)])
        client = TestClient(app)

        response = client.get(f"/api/v1/payments/{payment_id}")
        assert response.status_code == 404

    @pytest.mark.asyncio
    @patch("gateway.api.payments.httpx.AsyncClient")
    @patch("gateway.api.payments.create_payment_log")
    @patch("gateway.api.payments.finalize_payment_log")
    async def test_create_payment_service_error(self, mock_finalize, mock_create_log, mock_client_class, mock_merchant):
        """Test payment creation with service error."""
        from httpx import HTTPStatusError
        
        merchant_id = mock_merchant.merchant_id
        request_id = uuid4()
        mock_create_log.return_value = request_id
        
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.text = "Internal server error"

        mock_client = AsyncMock()
        mock_client.__aenter__.return_value = mock_client
        mock_client.__aexit__.return_value = None
        error = HTTPStatusError("Server error", request=MagicMock(), response=mock_response)
        mock_client.post = AsyncMock(side_effect=error)
        mock_client_class.return_value = mock_client

        from fastapi import FastAPI, Depends
        from fastapi.testclient import TestClient

        async def get_current_merchant():
            return mock_merchant

        app = FastAPI()
        app.include_router(payments_router, prefix="/api/v1/payments", dependencies=[Depends(get_current_merchant)])
        client = TestClient(app)

        payment_request = {
            "merchant_id": str(merchant_id),
            "amount": "100.00",
            "currency": "USD",
            "payment_method": "card",
        }

        response = client.post("/api/v1/payments", json=payment_request)
        assert response.status_code == 500
        mock_finalize.assert_called_once()

    @pytest.mark.asyncio
    @patch("gateway.api.payments.httpx.AsyncClient")
    @patch("gateway.api.payments.create_payment_log")
    @patch("gateway.api.payments.finalize_payment_log")
    async def test_create_payment_request_error(self, mock_finalize, mock_create_log, mock_client_class, mock_merchant):
        """Test payment creation with request error."""
        from httpx import RequestError
        
        merchant_id = mock_merchant.merchant_id
        request_id = uuid4()
        mock_create_log.return_value = request_id

        mock_client = AsyncMock()
        mock_client.__aenter__.return_value = mock_client
        mock_client.__aexit__.return_value = None
        error = RequestError("Connection error", request=MagicMock())
        mock_client.post = AsyncMock(side_effect=error)
        mock_client_class.return_value = mock_client

        from fastapi import FastAPI, Depends
        from fastapi.testclient import TestClient

        async def get_current_merchant():
            return mock_merchant

        app = FastAPI()
        app.include_router(payments_router, prefix="/api/v1/payments", dependencies=[Depends(get_current_merchant)])
        client = TestClient(app)

        payment_request = {
            "merchant_id": str(merchant_id),
            "amount": "100.00",
            "currency": "USD",
            "payment_method": "card",
        }

        response = client.post("/api/v1/payments", json=payment_request)
        assert response.status_code == 503
        mock_finalize.assert_called_once()

    @pytest.mark.asyncio
    @patch("gateway.api.payments.httpx.AsyncClient")
    async def test_get_payment_service_error(self, mock_client_class, mock_merchant):
        """Test get payment with service error."""
        from httpx import HTTPStatusError
        
        payment_id = uuid4()
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.text = "Server error"

        mock_client = AsyncMock()
        mock_client.__aenter__.return_value = mock_client
        mock_client.__aexit__.return_value = None
        error = HTTPStatusError("Server error", request=MagicMock(), response=mock_response)
        mock_client.get = AsyncMock(side_effect=error)
        mock_client_class.return_value = mock_client

        from fastapi import FastAPI, Depends
        from fastapi.testclient import TestClient

        async def get_current_merchant():
            return mock_merchant

        app = FastAPI()
        app.include_router(payments_router, prefix="/api/v1/payments", dependencies=[Depends(get_current_merchant)])
        client = TestClient(app)

        response = client.get(f"/api/v1/payments/{payment_id}")
        assert response.status_code == 500

    @pytest.mark.asyncio
    @patch("gateway.api.payments.httpx.AsyncClient")
    async def test_get_payment_request_error(self, mock_client_class, mock_merchant):
        """Test get payment with request error."""
        from httpx import RequestError
        
        payment_id = uuid4()

        mock_client = AsyncMock()
        mock_client.__aenter__.return_value = mock_client
        mock_client.__aexit__.return_value = None
        error = RequestError("Connection error", request=MagicMock())
        mock_client.get = AsyncMock(side_effect=error)
        mock_client_class.return_value = mock_client

        from fastapi import FastAPI, Depends
        from fastapi.testclient import TestClient

        async def get_current_merchant():
            return mock_merchant

        app = FastAPI()
        app.include_router(payments_router, prefix="/api/v1/payments", dependencies=[Depends(get_current_merchant)])
        client = TestClient(app)

        response = client.get(f"/api/v1/payments/{payment_id}")
        assert response.status_code == 503

    @pytest.mark.asyncio
    @patch("gateway.api.merchants.httpx.AsyncClient")
    async def test_create_merchant_request_error(self, mock_client_class):
        """Test create merchant with request error."""
        from httpx import RequestError

        mock_client = AsyncMock()
        mock_client.__aenter__.return_value = mock_client
        mock_client.__aexit__.return_value = None
        error = RequestError("Connection error", request=MagicMock())
        mock_client.post = AsyncMock(side_effect=error)
        mock_client_class.return_value = mock_client

        from fastapi import FastAPI
        from fastapi.testclient import TestClient

        app = FastAPI()
        app.include_router(merchants_router, prefix="/api/v1/merchants")
        client = TestClient(app)

        merchant_create = {
            "name": "Test Merchant",
            "email": "test@example.com",
        }

        response = client.post("/api/v1/merchants", json=merchant_create)
        assert response.status_code == 503
        assert "unavailable" in response.json()["detail"].lower()

    @pytest.mark.asyncio
    @patch("gateway.api.merchants.httpx.AsyncClient")
    async def test_get_merchant_request_error(self, mock_client_class):
        """Test get merchant with request error."""
        from httpx import RequestError

        merchant_id = uuid4()
        mock_client = AsyncMock()
        mock_client.__aenter__.return_value = mock_client
        mock_client.__aexit__.return_value = None
        error = RequestError("Connection error", request=MagicMock())
        mock_client.get = AsyncMock(side_effect=error)
        mock_client_class.return_value = mock_client

        from fastapi import FastAPI
        from fastapi.testclient import TestClient

        app = FastAPI()
        app.include_router(merchants_router, prefix="/api/v1/merchants")
        client = TestClient(app)

        response = client.get(f"/api/v1/merchants/{merchant_id}")
        assert response.status_code == 503
        assert "unavailable" in response.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_options_payment(self):
        """Test OPTIONS endpoint for payments."""
        from fastapi import FastAPI
        from fastapi.testclient import TestClient

        app = FastAPI()
        app.include_router(payments_router, prefix="/api/v1/payments")
        client = TestClient(app)

        response = client.options("/api/v1/payments")
        assert response.status_code == 200

        response = client.options("/api/v1/payments/")
        assert response.status_code == 200

    @pytest.mark.asyncio
    @patch("gateway.api.payments.httpx.AsyncClient")
    async def test_get_payment_with_query_param_api_key(self, mock_client_class):
        """Test get payment with API key from query parameter."""
        payment_id = uuid4()
        merchant_id = uuid4()
        now = datetime.utcnow()
        
        # Mock merchant service response
        mock_merchant_response = MagicMock()
        mock_merchant_response.status_code = 200
        mock_merchant_response.json.return_value = {
            "merchant_id": str(merchant_id),
            "name": "Test Merchant",
            "email": "test@example.com",
            "status": "active",
            "api_key": "sk_test_123",
            "created_at": now.isoformat(),
            "updated_at": now.isoformat(),
        }
        mock_merchant_response.raise_for_status = MagicMock()

        # Mock payment service response
        mock_payment_response = MagicMock()
        mock_payment_response.status_code = 200
        mock_payment_response.json.return_value = {
            "payment_id": str(payment_id),
            "merchant_id": str(merchant_id),
            "amount": "100.00",
            "currency": "USD",
            "status": "succeeded",
            "payment_method": "card",
            "created_at": now.isoformat(),
            "updated_at": now.isoformat(),
            "requires_action": False,
        }
        mock_payment_response.raise_for_status = MagicMock()

        mock_client = AsyncMock()
        mock_client.__aenter__.return_value = mock_client
        mock_client.__aexit__.return_value = None
        
        # First call for merchant service, second for payment service
        mock_client.get = AsyncMock(side_effect=[mock_merchant_response, mock_payment_response])
        mock_client_class.return_value = mock_client

        from fastapi import FastAPI
        from fastapi.testclient import TestClient

        app = FastAPI()
        app.include_router(payments_router, prefix="/api/v1/payments")
        client = TestClient(app)

        response = client.get(f"/api/v1/payments/{payment_id}?api_key=sk_test_123")
        assert response.status_code == 200
        assert response.json()["payment_id"] == str(payment_id)

    @pytest.mark.asyncio
    @patch("gateway.api.payments.httpx.AsyncClient")
    async def test_get_payment_merchant_service_401(self, mock_client_class):
        """Test get payment when merchant service returns 401."""
        payment_id = uuid4()
        from httpx import HTTPStatusError

        mock_response = MagicMock()
        mock_response.status_code = 401
        mock_response.text = "Unauthorized"

        mock_client = AsyncMock()
        mock_client.__aenter__.return_value = mock_client
        mock_client.__aexit__.return_value = None
        error = HTTPStatusError("Unauthorized", request=MagicMock(), response=mock_response)
        mock_client.get = AsyncMock(side_effect=error)
        mock_client_class.return_value = mock_client

        from fastapi import FastAPI
        from fastapi.testclient import TestClient

        app = FastAPI()
        app.include_router(payments_router, prefix="/api/v1/payments")
        client = TestClient(app)

        response = client.get(f"/api/v1/payments/{payment_id}", headers={"X-API-Key": "sk_test_123"})
        assert response.status_code == 401
        assert "Invalid API key" in response.json()["detail"]

    @pytest.mark.asyncio
    @patch("gateway.api.payments.httpx.AsyncClient")
    async def test_get_payment_merchant_service_404(self, mock_client_class):
        """Test get payment when merchant service returns 404."""
        payment_id = uuid4()
        from httpx import HTTPStatusError

        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_response.text = "Not found"

        mock_client = AsyncMock()
        mock_client.__aenter__.return_value = mock_client
        mock_client.__aexit__.return_value = None
        error = HTTPStatusError("Not found", request=MagicMock(), response=mock_response)
        mock_client.get = AsyncMock(side_effect=error)
        mock_client_class.return_value = mock_client

        from fastapi import FastAPI
        from fastapi.testclient import TestClient

        app = FastAPI()
        app.include_router(payments_router, prefix="/api/v1/payments")
        client = TestClient(app)

        response = client.get(f"/api/v1/payments/{payment_id}", headers={"X-API-Key": "sk_test_123"})
        assert response.status_code == 401
        assert "Invalid API key" in response.json()["detail"]


