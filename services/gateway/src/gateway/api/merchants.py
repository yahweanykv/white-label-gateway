"""Merchant API routes."""

from fastapi import APIRouter, HTTPException, status
from uuid import UUID

import httpx

from gateway.config import settings
from shared.models.merchant import Merchant, MerchantCreate

router = APIRouter()


@router.post("/", response_model=Merchant, status_code=status.HTTP_201_CREATED)
async def create_merchant(merchant_create: MerchantCreate):
    """
    Create a new merchant.

    Args:
        merchant_create: Merchant creation data

    Returns:
        Created merchant
    """
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                f"{settings.merchant_service_url}/api/v1/merchants",
                json=merchant_create.model_dump(),
                timeout=30.0,
            )
            response.raise_for_status()
            return Merchant(**response.json())
        except httpx.HTTPStatusError as e:
            raise HTTPException(
                status_code=e.response.status_code,
                detail=f"Merchant service error: {e.response.text}",
            )
        except httpx.RequestError as e:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"Merchant service unavailable: {str(e)}",
            )


@router.get("/{merchant_id}", response_model=Merchant)
async def get_merchant(merchant_id: UUID):
    """
    Get merchant by ID.

    Args:
        merchant_id: Merchant ID

    Returns:
        Merchant data
    """
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(
                f"{settings.merchant_service_url}/api/v1/merchants/{merchant_id}",
                timeout=30.0,
            )
            response.raise_for_status()
            return Merchant(**response.json())
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Merchant not found",
                )
            raise HTTPException(
                status_code=e.response.status_code,
                detail=f"Merchant service error: {e.response.text}",
            )
        except httpx.RequestError as e:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"Merchant service unavailable: {str(e)}",
            )

