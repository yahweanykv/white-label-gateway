"""Unit tests for gateway audit module."""

from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from gateway.audit import create_payment_log, finalize_payment_log
from shared.models.db import GatewayPaymentLog


@pytest.mark.asyncio
@patch("gateway.audit.db")
async def test_create_payment_log(mock_db):
    """Test creating payment log."""
    merchant_id = uuid4()
    request_id = uuid4()
    
    mock_session = AsyncMock(spec=AsyncSession)
    mock_entry = MagicMock()
    mock_entry.request_id = request_id
    mock_session.add = MagicMock()
    mock_session.flush = AsyncMock()
    
    mock_db.get_session.return_value.__aenter__.return_value = mock_session
    mock_db.get_session.return_value.__aexit__.return_value = None
    
    # Mock GatewayPaymentLog to return our mock entry
    with patch("gateway.audit.GatewayPaymentLog", return_value=mock_entry):
        result = await create_payment_log(
            merchant_id=merchant_id,
            path="/v1/payments",
            method="POST",
            request_payload={"amount": "100.00"},
        )
    
    assert result == request_id
    mock_session.add.assert_called_once()
    mock_session.flush.assert_called_once()


@pytest.mark.asyncio
@patch("gateway.audit.db")
async def test_finalize_payment_log_success(mock_db):
    """Test finalizing payment log successfully."""
    merchant_id = uuid4()
    request_id = uuid4()
    
    mock_entry = MagicMock()
    mock_entry.mark_response = MagicMock()
    
    mock_session = AsyncMock(spec=AsyncSession)
    mock_session.get = AsyncMock(return_value=mock_entry)
    
    mock_db.get_session.return_value.__aenter__.return_value = mock_session
    mock_db.get_session.return_value.__aexit__.return_value = None
    
    await finalize_payment_log(
        merchant_id=merchant_id,
        request_id=request_id,
        status_code=201,
        response_payload={"payment_id": str(uuid4())},
        payment_id=uuid4(),
    )
    
    mock_entry.mark_response.assert_called_once()


@pytest.mark.asyncio
@patch("gateway.audit.db")
async def test_finalize_payment_log_not_found(mock_db):
    """Test finalizing payment log when entry not found."""
    from sqlalchemy import select
    
    merchant_id = uuid4()
    request_id = uuid4()
    
    mock_session = AsyncMock(spec=AsyncSession)
    mock_session.get = AsyncMock(return_value=None)
    mock_result = MagicMock()
    mock_result.scalar_one_or_none = MagicMock(return_value=None)
    mock_session.execute = AsyncMock(return_value=mock_result)
    
    mock_db.get_session.return_value.__aenter__.return_value = mock_session
    mock_db.get_session.return_value.__aexit__.return_value = None
    
    # Should not raise error
    await finalize_payment_log(
        merchant_id=merchant_id,
        request_id=request_id,
        status_code=201,
        response_payload={"payment_id": str(uuid4())},
    )

