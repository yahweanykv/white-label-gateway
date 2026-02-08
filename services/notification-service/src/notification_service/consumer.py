"""RabbitMQ consumer for payment events."""

import asyncio
import json
from typing import Optional

import aio_pika
from aio_pika import IncomingMessage
from shared.utils.logger import setup_logger

from notification_service.config import settings
from notification_service.models import PaymentEvent, DeliveryAttempt, NotificationType, DeliveryStatus
from notification_service.webhook import send_webhook
from notification_service.email import send_email
from notification_service.retry import retry_with_backoff

logger = setup_logger(__name__)


async def get_merchant_webhook_url(merchant_id: str) -> Optional[str]:
    """
    Get webhook URL for merchant.

    Args:
        merchant_id: Merchant ID

    Returns:
        Webhook URL or None
    """
    import httpx

    try:
        async with httpx.AsyncClient() as client:
            # Try to get merchant by ID
            response = await client.get(
                f"{settings.merchant_service_url}/api/v1/merchants/{merchant_id}",
                timeout=5.0,
            )
            if response.is_success:
                merchant_data = response.json()
                webhook_url = merchant_data.get("webhook_url")
                if webhook_url:
                    return webhook_url
                logger.debug(f"Merchant {merchant_id} has no webhook_url configured")
            else:
                logger.warning(
                    f"Failed to fetch merchant {merchant_id}: status={response.status_code}"
                )
    except httpx.TimeoutException:
        logger.error(f"Timeout fetching merchant webhook URL for {merchant_id}")
    except Exception as e:
        logger.error(f"Error fetching merchant webhook URL for {merchant_id}: {e}")
    return None


async def process_payment_event(event: PaymentEvent) -> None:
    """
    Process payment event and send notifications.

    Args:
        event: Payment event
    """
    logger.info(f"Processing payment event: {event.event_type} for payment {event.payment_id}")

    delivery_attempts = []

    # Prepare payload
    payload = {
        "event_type": event.event_type,
        "payment_id": str(event.payment_id),
        "merchant_id": str(event.merchant_id),
        "amount": event.amount,
        "currency": event.currency,
        "status": event.status,
        "timestamp": event.timestamp.isoformat(),
        "metadata": event.metadata or {},
    }

    # Send webhook if merchant has webhook_url
    webhook_url = await get_merchant_webhook_url(str(event.merchant_id))
    if webhook_url:
        logger.info(f"Sending webhook to {webhook_url}")

        # Track attempts manually for logging
        webhook_attempts = []

        async def send_webhook_attempt():
            success, status_code, error = await send_webhook(
                webhook_url, payload, settings.webhook_secret
            )
            # Log this attempt
            attempt_num = len(webhook_attempts) + 1
            if success:
                webhook_attempts.append(
                    DeliveryAttempt(
                        attempt_number=attempt_num,
                        notification_type=NotificationType.WEBHOOK,
                        status=DeliveryStatus.SUCCESS,
                        response_code=status_code,
                    )
                )
                logger.info(
                    f"Webhook delivery attempt {attempt_num}: SUCCESS, "
                    f"response_code={status_code}"
                )
            else:
                status = (
                    DeliveryStatus.RETRYING
                    if attempt_num < settings.max_retries
                    else DeliveryStatus.FAILED
                )
                webhook_attempts.append(
                    DeliveryAttempt(
                        attempt_number=attempt_num,
                        notification_type=NotificationType.WEBHOOK,
                        status=status,
                        error_message=error,
                        response_code=status_code,
                    )
                )
                logger.warning(
                    f"Webhook delivery attempt {attempt_num}: {status}, "
                    f"response_code={status_code}, error={error}"
                )
            return success, status_code, error

        success, result, error = await retry_with_backoff(
            send_webhook_attempt,
            max_retries=settings.max_retries,
            base_delay=settings.retry_base_delay,
        )

        delivery_attempts.extend(webhook_attempts)

    # Send email if customer_email is provided
    if event.customer_email:
        logger.info(f"Sending email to {event.customer_email}")

        # Prepare email content
        if event.event_type == "payment.succeeded":
            subject = f"Payment Successful - {event.amount} {event.currency}"
            body = f"""
Your payment of {event.amount} {event.currency} has been successfully processed.

Payment ID: {event.payment_id}
Status: {event.status}

Thank you for your payment!
"""
        else:  # payment.failed
            subject = f"Payment Failed - {event.amount} {event.currency}"
            body = f"""
Your payment of {event.amount} {event.currency} could not be processed.

Payment ID: {event.payment_id}
Status: {event.status}

Please try again or contact support.
"""

        # Track attempts manually for logging
        email_attempts = []

        async def send_email_attempt():
            success, error = await send_email(
                smtp_host=settings.smtp_host,
                smtp_port=settings.smtp_port,
                smtp_user=settings.smtp_user,
                smtp_password=settings.smtp_password,
                from_email=settings.smtp_from_email,
                to_email=event.customer_email,
                subject=subject,
                body=body,
                use_tls=settings.smtp_use_tls,
            )
            # Log this attempt
            attempt_num = len(email_attempts) + 1
            if success:
                email_attempts.append(
                    DeliveryAttempt(
                        attempt_number=attempt_num,
                        notification_type=NotificationType.EMAIL,
                        status=DeliveryStatus.SUCCESS,
                    )
                )
                logger.info(f"Email delivery attempt {attempt_num}: SUCCESS")
            else:
                status = (
                    DeliveryStatus.RETRYING
                    if attempt_num < settings.max_retries
                    else DeliveryStatus.FAILED
                )
                email_attempts.append(
                    DeliveryAttempt(
                        attempt_number=attempt_num,
                        notification_type=NotificationType.EMAIL,
                        status=status,
                        error_message=error,
                    )
                )
                logger.warning(
                    f"Email delivery attempt {attempt_num}: {status}, error={error}"
                )
            return success, None, error

        success, result, error = await retry_with_backoff(
            send_email_attempt,
            max_retries=settings.max_retries,
            base_delay=settings.retry_base_delay,
        )

        delivery_attempts.extend(email_attempts)


async def process_message(message: IncomingMessage) -> None:
    """
    Process incoming RabbitMQ message.

    Args:
        message: Incoming message
    """
    async with message.process():
        try:
            body = message.body.decode("utf-8")
            data = json.loads(body)

            # Parse payment event
            event = PaymentEvent(**data)

            # Process event
            await process_payment_event(event)

            logger.info(f"Successfully processed message: {event.event_type}")

        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in message: {e}")
        except Exception as e:
            logger.error(f"Error processing message: {e}", exc_info=True)
            # Re-raise to reject message
            raise


async def start_consumer() -> None:
    """Start RabbitMQ consumer."""
    logger.info("Starting RabbitMQ consumer...")

    try:
        # Connect to RabbitMQ
        connection = await aio_pika.connect_robust(settings.rabbitmq_url)
        logger.info("Connected to RabbitMQ")

        # Create channel
        channel = await connection.channel()

        # Declare queues
        payment_succeeded_queue = await channel.declare_queue(
            "payment.succeeded", durable=True
        )
        payment_failed_queue = await channel.declare_queue("payment.failed", durable=True)

        logger.info("Queues declared: payment.succeeded, payment.failed")

        # Start consuming
        await payment_succeeded_queue.consume(process_message)
        await payment_failed_queue.consume(process_message)

        logger.info("Consumer started, waiting for messages...")

        # Keep connection alive
        try:
            await asyncio.Future()  # Run forever
        except KeyboardInterrupt:
            logger.info("Stopping consumer...")
        finally:
            await connection.close()
            logger.info("Consumer stopped")

    except Exception as e:
        logger.error(f"Error starting consumer: {e}", exc_info=True)
        raise

