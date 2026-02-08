"""Unit tests for merchant dashboard."""

from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from merchant_service.api.dashboard import get_dashboard, get_payment_stats, router
from merchant_service.models import Merchant


@pytest.fixture
def app():
    """Create test FastAPI app."""
    app = FastAPI()
    app.include_router(router, prefix="/api/v1")
    return app


@pytest.fixture
def mock_merchant():
    """Create mock merchant."""
    return Merchant(
        id=uuid4(),
        name="Test Merchant",
        domain="test.example.com",
        api_keys=["sk_test_123"],
        is_active=True,
        logo_url="https://example.com/logo.png",
        primary_color="#FF0000",
        background_color="#FFFFFF",
    )


@pytest.fixture
def client(app, mock_merchant):
    """Create test client with merchant dependency override."""
    from merchant_service.deps import get_current_merchant

    async def override_get_current_merchant():
        return mock_merchant

    app.dependency_overrides[get_current_merchant] = override_get_current_merchant
    return TestClient(app)


@pytest.mark.asyncio
@patch("merchant_service.api.dashboard.httpx.AsyncClient")
async def test_get_payment_stats_success(mock_client_class):
    """Test getting payment stats successfully."""
    mock_response = MagicMock()
    mock_response.json.return_value = [
        {"status": "succeeded", "amount": "100.00", "currency": "USD"},
        {"status": "succeeded", "amount": "50.00", "currency": "USD"},
        {"status": "processing", "amount": "25.00", "currency": "USD"},
    ]
    mock_response.raise_for_status = MagicMock()

    mock_client = AsyncMock()
    mock_client.__aenter__.return_value = mock_client
    mock_client.__aexit__.return_value = None
    mock_client.get = AsyncMock(return_value=mock_response)
    mock_client_class.return_value = mock_client

    stats = await get_payment_stats(str(uuid4()))

    assert stats["total"] == 3
    assert stats["successful"] == 2
    assert stats["pending"] == 1
    assert stats["currency"] == "USD"


@pytest.mark.asyncio
@patch("merchant_service.api.dashboard.httpx.AsyncClient")
async def test_get_payment_stats_service_error(mock_client_class):
    """Test getting payment stats with service error."""
    from httpx import HTTPError

    mock_client = AsyncMock()
    mock_client.__aenter__.return_value = mock_client
    mock_client.__aexit__.return_value = None
    error = HTTPError("Service unavailable")
    mock_client.get = AsyncMock(side_effect=error)
    mock_client_class.return_value = mock_client

    stats = await get_payment_stats(str(uuid4()))

    assert stats["total"] == 0
    assert stats["successful"] == 0
    assert stats["pending"] == 0


@pytest.mark.asyncio
@patch("merchant_service.api.dashboard.get_payment_stats")
async def test_get_dashboard_success(mock_get_stats, client, mock_merchant):
    """Test getting dashboard successfully."""
    mock_get_stats.return_value = {
        "total": 10,
        "successful": 8,
        "pending": 2,
        "revenue": 1000.00,
        "currency": "USD",
    }

    response = client.get("/api/v1/dashboard", headers={"X-API-Key": "sk_test_123"})
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert mock_merchant.name in response.text
    assert "10" in response.text  # total payments
    assert "8" in response.text  # successful payments


@pytest.mark.asyncio
@patch("merchant_service.api.dashboard.get_payment_stats")
async def test_get_dashboard_with_defaults(mock_get_stats, client):
    """Test getting dashboard with default colors."""
    from merchant_service.deps import get_current_merchant

    merchant_no_colors = Merchant(
        id=uuid4(),
        name="No Colors Merchant",
        domain="nocolors.example.com",
        api_keys=["sk_test_456"],
        is_active=True,
        logo_url=None,
        primary_color=None,
        background_color=None,
    )

    async def override_get_current_merchant():
        return merchant_no_colors

    client.app.dependency_overrides[get_current_merchant] = override_get_current_merchant

    mock_get_stats.return_value = {
        "total": 0,
        "successful": 0,
        "pending": 0,
        "revenue": 0.00,
        "currency": "USD",
    }

    response = client.get("/api/v1/dashboard", headers={"X-API-Key": "sk_test_456"})
    assert response.status_code == 200
    assert "#4F46E5" in response.text  # default primary color
