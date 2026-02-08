"""Unit tests for gateway router."""

from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from gateway.router import router
from shared.models.merchant import Merchant, MerchantStatus


class TestGatewayRouter:
    """Tests for gateway router."""

    @pytest.mark.asyncio
    async def test_health_check(self):
        """Test health check endpoint."""
        app = FastAPI()
        app.include_router(router)
        client = TestClient(app)

        response = client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "healthy", "service": "gateway"}

    @pytest.mark.asyncio
    async def test_get_current_user_info(self):
        """Test get current user info endpoint."""
        from gateway.deps import get_current_merchant
        
        now = datetime.utcnow()
        mock_merchant = Merchant(
            merchant_id=uuid4(),
            name="Test Merchant",
            email="test@example.com",
            status=MerchantStatus.ACTIVE,
            api_key="sk_test_123",
            created_at=now,
            updated_at=now,
        )

        async def mock_get_current_merchant():
            return mock_merchant

        app = FastAPI()
        app.dependency_overrides[get_current_merchant] = mock_get_current_merchant
        app.include_router(router)
        client = TestClient(app)

        try:
            response = client.get("/v1/me")
            assert response.status_code == 200
            data = response.json()
            assert data["merchant_id"] == str(mock_merchant.merchant_id)
            assert data["name"] == mock_merchant.name
            assert data["email"] == mock_merchant.email
            assert data["status"] == mock_merchant.status.value
        finally:
            app.dependency_overrides.pop(get_current_merchant, None)
