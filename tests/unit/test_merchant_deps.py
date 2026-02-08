"""Unit tests for merchant service dependencies."""

from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from merchant_service.deps import get_current_merchant
from merchant_service.models import Merchant


@pytest.mark.asyncio
async def test_get_current_merchant_success():
    """Test getting current merchant successfully."""
    api_key = "sk_test_123"
    merchant = Merchant(
        id=uuid4(),
        name="Test Merchant",
        domain="test.example.com",
        api_keys=[api_key],
        is_active=True,
    )

    mock_db = AsyncMock(spec=AsyncSession)
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = merchant
    mock_db.execute = AsyncMock(return_value=mock_result)

    result = await get_current_merchant(x_api_key=api_key, db=mock_db)

    assert result == merchant
    mock_db.execute.assert_called_once()


@pytest.mark.asyncio
async def test_get_current_merchant_no_api_key():
    """Test getting current merchant without API key."""
    mock_db = AsyncMock(spec=AsyncSession)

    with pytest.raises(HTTPException) as exc_info:
        await get_current_merchant(x_api_key=None, db=mock_db)

    assert exc_info.value.status_code == 401
    assert "X-API-Key" in exc_info.value.detail


@pytest.mark.asyncio
async def test_get_current_merchant_not_found():
    """Test getting current merchant with invalid API key."""
    mock_db = AsyncMock(spec=AsyncSession)
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None
    mock_db.execute = AsyncMock(return_value=mock_result)

    with pytest.raises(HTTPException) as exc_info:
        await get_current_merchant(x_api_key="invalid_key", db=mock_db)

    assert exc_info.value.status_code == 401
    assert "Invalid API key" in exc_info.value.detail


@pytest.mark.asyncio
async def test_get_current_merchant_inactive():
    """Test getting current merchant that is inactive."""
    api_key = "sk_test_123"
    merchant = Merchant(
        id=uuid4(),
        name="Inactive Merchant",
        domain="inactive.example.com",
        api_keys=[api_key],
        is_active=False,
    )

    mock_db = AsyncMock(spec=AsyncSession)
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None  # Query filters by is_active=True
    mock_db.execute = AsyncMock(return_value=mock_result)

    with pytest.raises(HTTPException) as exc_info:
        await get_current_merchant(x_api_key=api_key, db=mock_db)

    assert exc_info.value.status_code == 401
