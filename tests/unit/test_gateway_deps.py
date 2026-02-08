"""Unit tests for gateway dependencies."""

from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest
from fastapi import HTTPException, Request
from gateway.deps import get_current_merchant
from httpx import HTTPStatusError, RequestError

from shared.models.merchant import MerchantStatus


@pytest.mark.asyncio
@patch("gateway.deps.get_redis")
@patch("gateway.deps.httpx.AsyncClient")
async def test_get_current_merchant_success(mock_client_class, mock_get_redis):
    """Test getting current merchant successfully."""
    mock_redis = AsyncMock()
    mock_redis.connect = AsyncMock()
    mock_redis.get_json = AsyncMock(return_value=None)  # cache miss
    mock_redis.set_json = AsyncMock()
    mock_get_redis.return_value = mock_redis
    merchant_id = uuid4()
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "merchant_id": str(merchant_id),
        "name": "Test Merchant",
        "email": "test@example.com",
        "status": "active",
        "api_key": "sk_test_123",
        "created_at": "2024-01-01T00:00:00",
        "updated_at": "2024-01-01T00:00:00",
    }
    mock_response.status_code = 200
    mock_response.raise_for_status = MagicMock()

    mock_client = AsyncMock()
    mock_client.__aenter__.return_value = mock_client
    mock_client.__aexit__.return_value = None
    mock_client.get = AsyncMock(return_value=mock_response)
    mock_client_class.return_value = mock_client

    request = MagicMock(spec=Request)
    request.state = MagicMock()

    merchant = await get_current_merchant(request, x_api_key="sk_test_123")

    assert merchant.merchant_id == merchant_id
    assert merchant.status == MerchantStatus.ACTIVE
    assert request.state.merchant_id == merchant_id


@pytest.mark.asyncio
@patch("gateway.deps.get_redis")
async def test_get_current_merchant_cache_hit(mock_get_redis):
    """Test getting current merchant from cache."""
    merchant_id = uuid4()
    cached_data = {
        "merchant_id": str(merchant_id),
        "name": "Cached Merchant",
        "email": "cached@example.com",
        "status": "active",
        "api_key": "sk_test_123",
        "created_at": "2024-01-01T00:00:00",
        "updated_at": "2024-01-01T00:00:00",
    }

    mock_redis = AsyncMock()
    mock_redis.connect = AsyncMock()
    mock_redis.get_json = AsyncMock(return_value=cached_data)
    mock_get_redis.return_value = mock_redis

    request = MagicMock(spec=Request)
    request.state = MagicMock()

    merchant = await get_current_merchant(request, x_api_key="sk_test_123")

    assert merchant.merchant_id == merchant_id
    assert merchant.name == "Cached Merchant"
    assert request.state.merchant_id == merchant_id
    mock_redis.get_json.assert_called_once()


@pytest.mark.asyncio
async def test_get_current_merchant_no_api_key():
    """Test getting current merchant without API key."""
    request = MagicMock(spec=Request)

    with pytest.raises(HTTPException) as exc_info:
        await get_current_merchant(request, x_api_key=None)

    assert exc_info.value.status_code == 401
    assert "X-API-Key" in exc_info.value.detail


@pytest.mark.asyncio
@patch("gateway.deps.get_redis")
@patch("gateway.deps.httpx.AsyncClient")
async def test_get_current_merchant_not_found(mock_client_class, mock_get_redis):
    """Test getting current merchant with invalid API key."""
    mock_response = MagicMock()
    mock_response.status_code = 404

    mock_client = AsyncMock()
    mock_client.__aenter__.return_value = mock_client
    mock_client.__aexit__.return_value = None
    mock_client.get = AsyncMock(return_value=mock_response)
    mock_client_class.return_value = mock_client

    request = MagicMock(spec=Request)

    with pytest.raises(HTTPException) as exc_info:
        await get_current_merchant(request, x_api_key="invalid_key")

    assert exc_info.value.status_code == 401


@pytest.mark.asyncio
@patch("gateway.deps.get_redis")
@patch("gateway.deps.httpx.AsyncClient")
async def test_get_current_merchant_inactive(mock_client_class, mock_get_redis):
    """Test getting current merchant with inactive status."""
    merchant_id = uuid4()
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "merchant_id": str(merchant_id),
        "name": "Test Merchant",
        "email": "test@example.com",
        "status": "inactive",
        "api_key": "sk_test_123",
        "created_at": "2024-01-01T00:00:00",
        "updated_at": "2024-01-01T00:00:00",
    }
    mock_response.status_code = 200
    mock_response.raise_for_status = MagicMock()

    mock_client = AsyncMock()
    mock_client.__aenter__.return_value = mock_client
    mock_client.__aexit__.return_value = None
    mock_client.get = AsyncMock(return_value=mock_response)
    mock_client_class.return_value = mock_client

    request = MagicMock(spec=Request)

    with pytest.raises(HTTPException) as exc_info:
        await get_current_merchant(request, x_api_key="sk_test_123")

    assert exc_info.value.status_code == 403


@pytest.mark.asyncio
@patch("gateway.deps.get_redis")
@patch("gateway.deps.httpx.AsyncClient")
async def test_get_current_merchant_service_error(mock_client_class, mock_get_redis):
    """Test getting current merchant with service error."""
    mock_response = MagicMock()
    mock_response.status_code = 500
    mock_response.text = "Server error"

    mock_client = AsyncMock()
    mock_client.__aenter__.return_value = mock_client
    mock_client.__aexit__.return_value = None
    error = HTTPStatusError("Server error", request=MagicMock(), response=mock_response)
    mock_client.get = AsyncMock(side_effect=error)
    mock_client_class.return_value = mock_client

    request = MagicMock(spec=Request)

    with pytest.raises(HTTPException) as exc_info:
        await get_current_merchant(request, x_api_key="sk_test_123")

    assert exc_info.value.status_code == 503


@pytest.mark.asyncio
@patch("gateway.deps.get_redis")
@patch("gateway.deps.httpx.AsyncClient")
async def test_get_current_merchant_request_error(mock_client_class, mock_get_redis):
    """Test getting current merchant with request error."""
    mock_redis = AsyncMock()
    mock_redis.connect = AsyncMock()
    mock_redis.get_json = AsyncMock(return_value=None)
    mock_get_redis.return_value = mock_redis

    mock_client = AsyncMock()
    mock_client.__aenter__.return_value = mock_client
    mock_client.__aexit__.return_value = None
    error = RequestError("Connection error", request=MagicMock())
    mock_client.get = AsyncMock(side_effect=error)
    mock_client_class.return_value = mock_client

    request = MagicMock(spec=Request)

    with pytest.raises(HTTPException) as exc_info:
        await get_current_merchant(request, x_api_key="sk_test_123")

    assert exc_info.value.status_code == 503
