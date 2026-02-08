"""Payment API routes."""

from typing import Annotated
from urllib.parse import urlencode
from uuid import UUID

import httpx
from fastapi import APIRouter, Depends, HTTPException, Request, status

from gateway.audit import create_payment_log, finalize_payment_log
from gateway.config import settings
from gateway.deps import get_current_merchant
from shared.models.merchant import Merchant
from shared.models.payment import PaymentRequest, PaymentResponse
from shared.utils.logger import setup_logger
import os

logger = setup_logger(
    __name__, level="INFO", json_logs=os.getenv("JSON_LOGS", "false").lower() == "true"
)

router = APIRouter()

DEFAULT_LOGO = "https://via.placeholder.com/120?text=Logo"
DEFAULT_PRIMARY_COLOR = "#4F46E5"
DEFAULT_BACKGROUND_COLOR = "#EEF2FF"


@router.options("")
@router.options("/")
async def options_payment():
    """
    Handle CORS preflight requests for payment endpoints.

    This endpoint is explicitly defined to ensure OPTIONS requests
    are handled before dependencies are called.
    """
    from fastapi.responses import Response

    return Response(status_code=200)


def _build_mock_query(payment: PaymentResponse, merchant: Merchant) -> str:
    params = {
        "paymentId": str(payment.payment_id),
        "merchantName": merchant.name,
        "logoUrl": merchant.logo_url or DEFAULT_LOGO,
        "primaryColor": merchant.primary_color or DEFAULT_PRIMARY_COLOR,
        "backgroundColor": merchant.background_color or DEFAULT_BACKGROUND_COLOR,
        "amount": str(payment.amount),
        "currency": payment.currency,
    }
    return urlencode(params)


def _enrich_with_next_action(payment: PaymentResponse, merchant: Merchant) -> PaymentResponse:
    if payment.requires_action and payment.next_action:
        action_type = payment.next_action.get("type")
        path = payment.next_action.get("path")
        if action_type == "redirect" and path == "/mock-3ds":
            query = _build_mock_query(payment, merchant)
            payment.next_action_url = f"/mock-3ds?{query}"
            payment.next_action = {
                **payment.next_action,
                "url": payment.next_action_url,
            }
    return payment


@router.post("", response_model=PaymentResponse, status_code=status.HTTP_201_CREATED)
@router.post("/", response_model=PaymentResponse, status_code=status.HTTP_201_CREATED)
async def create_payment(
    payment_request: PaymentRequest,
    request: Request,
    current_merchant: Annotated[Merchant, Depends(get_current_merchant)],
):
    """
    Create a new payment.

    Args:
        payment_request: Payment request data
        request: FastAPI request object
        current_merchant: Merchant context

    Returns:
        Created payment response
    """
    logger.info(f"Creating payment for merchant {current_merchant.merchant_id}")
    request_id = None
    try:
        request_id = await create_payment_log(
            merchant_id=current_merchant.merchant_id,
            path="/v1/payments",
            method="POST",
            request_payload=payment_request.model_dump(mode="json"),
        )
    except Exception as e:
        from uuid import uuid4

        logger.warning(f"Audit log failed, continuing: {e}")
        request_id = uuid4()

    # Get API key from request state (set by get_current_merchant)
    api_key = getattr(request.state, "api_key", None)
    headers = {}
    if api_key:
        headers["X-API-Key"] = api_key

    # Override merchant_id with the authenticated merchant's ID for security
    payment_data = payment_request.model_dump(mode="json")
    payment_data["merchant_id"] = str(current_merchant.merchant_id)

    payment_service_url = f"{settings.payment_service_url}/api/v1/payments"
    logger.info(f"Forwarding payment request to: {payment_service_url}")
    logger.debug(f"Payment data: {payment_data}, Headers: {headers}")

    async with httpx.AsyncClient(follow_redirects=True, timeout=30.0) as client:
        try:
            response = await client.post(
                payment_service_url,
                json=payment_data,
                headers=headers,
                timeout=30.0,
            )
            response.raise_for_status()
            resp_json = response.json()
            payment = PaymentResponse.model_validate(resp_json)
            enriched = _enrich_with_next_action(payment, current_merchant)
            try:
                await finalize_payment_log(
                    merchant_id=current_merchant.merchant_id,
                    request_id=request_id,
                    status_code=response.status_code,
                    response_payload=enriched.model_dump(mode="json"),
                    payment_id=enriched.payment_id,
                )
            except Exception as audit_err:
                logger.warning(f"Failed to finalize audit: {audit_err}")
            return enriched
        except httpx.HTTPStatusError as e:
            try:
                await finalize_payment_log(
                    merchant_id=current_merchant.merchant_id,
                    request_id=request_id,
                    status_code=e.response.status_code,
                    response_payload={"detail": e.response.text},
                )
            except Exception:
                pass
            raise HTTPException(
                status_code=e.response.status_code,
                detail=f"Payment service error: {e.response.text}",
            )
        except httpx.RequestError as e:
            error_msg = f"Payment service request error: {type(e).__name__}: {str(e)}"
            logger.error(
                error_msg,
                extra={
                    "payment_service_url": payment_service_url,
                    "error_type": type(e).__name__,
                    "error": str(e),
                    "merchant_id": str(current_merchant.merchant_id),
                },
            )
            try:
                await finalize_payment_log(
                    merchant_id=current_merchant.merchant_id,
                    request_id=request_id,
                    status_code=None,
                    response_payload=None,
                    error_message=str(e),
                )
            except Exception:
                pass
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"Payment service unavailable: {str(e)}",
            )


@router.get("/{payment_id}", response_model=PaymentResponse)
async def get_payment(
    payment_id: UUID,
    request: Request,
):
    """
    Get payment by ID.

    Can accept API key either via X-API-Key header or via api_key query parameter (for demo purposes).

    Args:
        payment_id: Payment ID
        request: FastAPI request object

    Returns:
        Payment response
    """
    # Try to get API key from header first
    x_api_key = (
        request.headers.get("X-API-Key")
        or request.headers.get("x-api-key")
        or request.headers.get("X-Api-Key")
    )

    # If no API key from header, try query parameter
    if not x_api_key:
        x_api_key = request.query_params.get("api_key")
        if x_api_key:
            logger.info(f"Got API key from query parameter: {x_api_key[:20]}...")

    # Log for debugging
    logger.info(
        f"Request to get payment {payment_id}, API key present: {bool(x_api_key)}, query params: {dict(request.query_params)}"
    )

    if not x_api_key:
        logger.warning(f"No API key found in headers or query params for payment {payment_id}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="X-API-Key header or api_key query parameter is required",
            headers={"WWW-Authenticate": "ApiKey"},
        )

    # Get merchant to verify and get merchant_id
    merchant_url = f"{settings.merchant_service_url}/api/v1/merchants/by-api-key"
    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            response = await client.get(
                merchant_url,
                headers={"X-API-Key": x_api_key},
                timeout=10.0,
            )
            if response.status_code == 404:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid API key",
                )
            response.raise_for_status()
            merchant_data = response.json()
            from shared.models.merchant import Merchant

            current_merchant = Merchant(**merchant_data)
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 401 or e.response.status_code == 404:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid API key",
                )
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"Merchant service error: {e.response.status_code}",
            )
        except httpx.RequestError as e:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"Merchant service unavailable: {str(e)}",
            )

    headers = {"X-API-Key": x_api_key}

    async with httpx.AsyncClient(follow_redirects=True) as client:
        try:
            response = await client.get(
                f"{settings.payment_service_url}/api/v1/payments/{payment_id}",
                headers=headers,
                timeout=30.0,
            )
            response.raise_for_status()
            payment = PaymentResponse(**response.json())

            # Enrich payment with merchant branding if merchant is available
            if current_merchant:
                return _enrich_with_next_action(payment, current_merchant)
            return payment
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Payment not found",
                )
            raise HTTPException(
                status_code=e.response.status_code,
                detail=f"Payment service error: {e.response.text}",
            )
        except httpx.RequestError as e:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"Payment service unavailable: {str(e)}",
            )
