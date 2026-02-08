"""API router with all routes."""

from fastapi import APIRouter, Depends
from typing import Annotated

from gateway.api.mock import router as mock_router
from gateway.api.payments import router as payments_router
from gateway.deps import get_current_merchant
from shared.models.merchant import Merchant

router = APIRouter()


@router.get("/health")
async def health_check():
    """
    Health check endpoint.

    Returns:
        Health status
    """
    return {"status": "healthy", "service": "gateway"}


# Include payment routes under /v1/payments
# Note: get_current_merchant dependency is applied at router level
router.include_router(
    payments_router,
    prefix="/v1/payments",
    tags=["payments"],
)
router.include_router(mock_router)


@router.get("/v1/me")
async def get_current_user_info(
    current_merchant: Annotated[Merchant, Depends(get_current_merchant)],
):
    """
    Get current merchant information.

    Args:
        current_merchant: Current merchant from dependency

    Returns:
        Merchant information
    """
    return {
        "merchant_id": str(current_merchant.merchant_id),
        "name": current_merchant.name,
        "email": current_merchant.email,
        "status": current_merchant.status,
    }
