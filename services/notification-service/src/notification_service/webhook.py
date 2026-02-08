"""Webhook delivery with HMAC-SHA256 signing."""

import hmac
import hashlib
import json
from typing import Dict, Any, Optional

import httpx
from shared.utils.logger import setup_logger

logger = setup_logger(__name__)


def generate_webhook_signature(payload: str, secret: str) -> str:
    """
    Generate HMAC-SHA256 signature for webhook payload.

    Args:
        payload: JSON string payload
        secret: Secret key for signing

    Returns:
        Hex-encoded signature
    """
    signature = hmac.new(
        secret.encode("utf-8"), payload.encode("utf-8"), hashlib.sha256
    ).hexdigest()
    return signature


async def send_webhook(
    url: str,
    payload: Dict[str, Any],
    secret: str,
    timeout: float = 10.0,
) -> tuple[bool, Optional[int], Optional[str]]:
    """
    Send webhook with HMAC-SHA256 signature.

    Args:
        url: Webhook URL
        payload: Payload dictionary
        secret: Secret key for signing
        timeout: Request timeout in seconds

    Returns:
        Tuple of (success, status_code, error_message)
    """
    try:
        # Serialize payload to JSON
        payload_json = json.dumps(payload, default=str, sort_keys=True)
        signature = generate_webhook_signature(payload_json, secret)

        headers = {
            "Content-Type": "application/json",
            "X-Webhook-Signature": f"sha256={signature}",
            "User-Agent": "PaymentGateway-Webhook/1.0",
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(
                url,
                content=payload_json,
                headers=headers,
                timeout=timeout,
            )

            if response.is_success:
                logger.info(
                    f"Webhook delivered successfully to {url}: status={response.status_code}"
                )
                return True, response.status_code, None
            else:
                error_msg = f"Webhook delivery failed: status={response.status_code}, body={response.text[:200]}"
                logger.warning(error_msg)
                return False, response.status_code, error_msg

    except httpx.TimeoutException:
        error_msg = f"Webhook delivery timeout for {url}"
        logger.error(error_msg)
        return False, None, error_msg
    except httpx.RequestError as e:
        error_msg = f"Webhook delivery error for {url}: {str(e)}"
        logger.error(error_msg)
        return False, None, error_msg
    except Exception as e:
        error_msg = f"Unexpected error sending webhook to {url}: {str(e)}"
        logger.error(error_msg)
        return False, None, error_msg

