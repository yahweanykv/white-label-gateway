"""External service integrations (Fraud, Notification, RabbitMQ)."""

from __future__ import annotations

import json
from typing import Any, Optional
from uuid import uuid4

import aio_pika
import httpx
from shared.models.payment import PaymentRequest, PaymentResponse, PaymentStatus
from shared.utils.logger import setup_logger

from payment_service.config import settings

logger = setup_logger(__name__)


async def perform_fraud_check(payment_request: PaymentRequest) -> Optional[dict[str, Any]]:
    """Call fraud-service to evaluate risk for the payment."""
    payload = {
        "payment_id": str(uuid4()),
        "merchant_id": str(payment_request.merchant_id),
        "amount": str(payment_request.amount),
        "currency": payment_request.currency,
        "customer_email": payment_request.customer_email,
        "metadata": payment_request.metadata or {},
    }
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.post(
                f"{settings.fraud_service_url}/api/v1/fraud/check",
                json=payload,
            )
            response.raise_for_status()
            return response.json()
    except httpx.HTTPError as exc:  # pragma: no cover - network failures
        logger.warning("Fraud service request failed: %s", exc)
        return None


async def notify_customer(payment: PaymentResponse, customer_email: Optional[str]) -> None:
    """Send notification via notification-service if customer email is provided."""
    if not customer_email:
        return

    body = (
        f"Payment {payment.payment_id} for {payment.amount} {payment.currency} "
        f"is {payment.status.value.upper()}."
    )
    payload = {
        "recipient": customer_email,
        "subject": f"Payment {payment.status.value}",
        "body": body,
        "notification_type": "email",
        "metadata": {"payment_id": str(payment.payment_id), "status": payment.status.value},
    }
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            await client.post(
                f"{settings.notification_service_url}/api/v1/notifications",
                json=payload,
            )
    except httpx.HTTPError as exc:  # pragma: no cover - network failures
        logger.warning("Notification service request failed: %s", exc)


async def publish_payment_event(
    payment: PaymentResponse,
    *,
    customer_email: Optional[str],
    metadata: Optional[dict[str, Any]],
) -> None:
    """Publish payment lifecycle event to RabbitMQ for notification-service."""
    if payment.status == PaymentStatus.SUCCEEDED:
        routing_key = "payment.succeeded"
    elif payment.status == PaymentStatus.FAILED:
        routing_key = "payment.failed"
    else:
        return

    event_payload = {
        "event_type": routing_key,
        "payment_id": str(payment.payment_id),
        "merchant_id": str(payment.merchant_id),
        "amount": str(payment.amount),
        "currency": payment.currency,
        "status": payment.status.value,
        "customer_email": customer_email,
        "metadata": metadata or {},
    }

    try:
        connection = await aio_pika.connect_robust(settings.rabbitmq_url)
        async with connection:
            channel = await connection.channel()
            queue = await channel.declare_queue(routing_key, durable=True)
            message = aio_pika.Message(
                body=json.dumps(event_payload).encode("utf-8"),
                content_type="application/json",
            )
            await channel.default_exchange.publish(message, routing_key=queue.name)
    except Exception as exc:  # pragma: no cover - broker failures
        logger.warning("Failed to publish payment event: %s", exc)



