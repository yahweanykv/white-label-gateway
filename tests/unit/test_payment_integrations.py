"""Unit tests for payment service integrations."""

from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest
from payment_service.integrations import (
    notify_customer,
    perform_fraud_check,
    publish_payment_event,
)

from shared.models.payment import PaymentMethod, PaymentRequest, PaymentResponse, PaymentStatus


@pytest.mark.asyncio
@patch("payment_service.integrations.httpx.AsyncClient")
async def test_perform_fraud_check_success(mock_client_class):
    """Test successful fraud check."""
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "is_fraud": False,
        "risk_score": 0.1,
        "reason": None,
    }
    mock_response.raise_for_status = MagicMock()

    mock_client = AsyncMock()
    mock_client.__aenter__.return_value = mock_client
    mock_client.__aexit__.return_value = None
    mock_client.post = AsyncMock(return_value=mock_response)
    mock_client_class.return_value = mock_client

    payment_request = PaymentRequest(
        merchant_id=uuid4(),
        amount=Decimal("100.00"),
        currency="USD",
        payment_method=PaymentMethod.CARD,
    )

    result = await perform_fraud_check(payment_request)

    assert result is not None
    assert result["is_fraud"] is False
    assert result["risk_score"] == 0.1


@pytest.mark.asyncio
@patch("payment_service.integrations.httpx.AsyncClient")
async def test_perform_fraud_check_fraud_detected(mock_client_class):
    """Test fraud check with fraud detected."""
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "is_fraud": True,
        "risk_score": 0.9,
        "reason": "High risk transaction",
    }
    mock_response.raise_for_status = MagicMock()

    mock_client = AsyncMock()
    mock_client.__aenter__.return_value = mock_client
    mock_client.__aexit__.return_value = None
    mock_client.post = AsyncMock(return_value=mock_response)
    mock_client_class.return_value = mock_client

    payment_request = PaymentRequest(
        merchant_id=uuid4(),
        amount=Decimal("1000.00"),
        currency="USD",
        payment_method=PaymentMethod.CARD,
    )

    result = await perform_fraud_check(payment_request)

    assert result is not None
    assert result["is_fraud"] is True


@pytest.mark.asyncio
@patch("payment_service.integrations.httpx.AsyncClient")
async def test_perform_fraud_check_service_error(mock_client_class):
    """Test fraud check with service error."""
    from httpx import HTTPError

    mock_client = AsyncMock()
    mock_client.__aenter__.return_value = mock_client
    mock_client.__aexit__.return_value = None
    error = HTTPError("Service unavailable")
    mock_client.post = AsyncMock(side_effect=error)
    mock_client_class.return_value = mock_client

    payment_request = PaymentRequest(
        merchant_id=uuid4(),
        amount=Decimal("100.00"),
        currency="USD",
        payment_method=PaymentMethod.CARD,
    )

    result = await perform_fraud_check(payment_request)

    assert result is None


@pytest.mark.asyncio
@patch("payment_service.integrations.httpx.AsyncClient")
async def test_notify_customer_success(mock_client_class):
    """Test successful customer notification."""
    from datetime import datetime

    mock_response = MagicMock()
    mock_response.status_code = 200

    mock_client = AsyncMock()
    mock_client.__aenter__.return_value = mock_client
    mock_client.__aexit__.return_value = None
    mock_client.post = AsyncMock(return_value=mock_response)
    mock_client_class.return_value = mock_client

    payment = PaymentResponse(
        payment_id=uuid4(),
        merchant_id=uuid4(),
        amount=Decimal("100.00"),
        currency="USD",
        status=PaymentStatus.SUCCEEDED,
        payment_method=PaymentMethod.CARD,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )

    await notify_customer(payment, "customer@example.com")

    mock_client.post.assert_called_once()


@pytest.mark.asyncio
async def test_notify_customer_no_email():
    """Test customer notification without email."""
    from datetime import datetime

    payment = PaymentResponse(
        payment_id=uuid4(),
        merchant_id=uuid4(),
        amount=Decimal("100.00"),
        currency="USD",
        status=PaymentStatus.SUCCEEDED,
        payment_method=PaymentMethod.CARD,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )

    # Should not raise error and not call service
    await notify_customer(payment, None)


@pytest.mark.asyncio
@patch("payment_service.integrations.aio_pika.connect_robust")
async def test_publish_payment_event_succeeded(mock_connect):
    """Test publishing succeeded payment event."""
    from datetime import datetime

    mock_connection = AsyncMock()
    mock_channel = AsyncMock()
    mock_queue = MagicMock()
    mock_queue.name = "payment.succeeded"

    mock_connection.__aenter__.return_value = mock_connection
    mock_connection.__aexit__.return_value = None
    mock_connection.channel = AsyncMock(return_value=mock_channel)
    mock_channel.declare_queue = AsyncMock(return_value=mock_queue)
    mock_channel.default_exchange.publish = AsyncMock()

    mock_connect.return_value = mock_connection

    payment = PaymentResponse(
        payment_id=uuid4(),
        merchant_id=uuid4(),
        amount=Decimal("100.00"),
        currency="USD",
        status=PaymentStatus.SUCCEEDED,
        payment_method=PaymentMethod.CARD,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )

    await publish_payment_event(payment, customer_email="customer@example.com", metadata={})

    mock_channel.default_exchange.publish.assert_called_once()


@pytest.mark.asyncio
@patch("payment_service.integrations.aio_pika.connect_robust")
async def test_publish_payment_event_failed(mock_connect):
    """Test publishing failed payment event."""
    from datetime import datetime

    mock_connection = AsyncMock()
    mock_channel = AsyncMock()
    mock_queue = MagicMock()
    mock_queue.name = "payment.failed"

    mock_connection.__aenter__.return_value = mock_connection
    mock_connection.__aexit__.return_value = None
    mock_connection.channel = AsyncMock(return_value=mock_channel)
    mock_channel.declare_queue = AsyncMock(return_value=mock_queue)
    mock_channel.default_exchange.publish = AsyncMock()

    mock_connect.return_value = mock_connection

    payment = PaymentResponse(
        payment_id=uuid4(),
        merchant_id=uuid4(),
        amount=Decimal("100.00"),
        currency="USD",
        status=PaymentStatus.FAILED,
        payment_method=PaymentMethod.CARD,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )

    await publish_payment_event(payment, customer_email="customer@example.com", metadata={})

    mock_channel.default_exchange.publish.assert_called_once()


@pytest.mark.asyncio
@patch("payment_service.integrations.aio_pika.connect_robust")
async def test_publish_payment_event_processing(mock_connect):
    """Test publishing processing payment event (should not publish)."""
    from datetime import datetime

    payment = PaymentResponse(
        payment_id=uuid4(),
        merchant_id=uuid4(),
        amount=Decimal("100.00"),
        currency="USD",
        status=PaymentStatus.PROCESSING,
        payment_method=PaymentMethod.CARD,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )

    await publish_payment_event(payment, customer_email="customer@example.com", metadata={})

    # Should not call connect_robust for processing status
    mock_connect.assert_not_called()
