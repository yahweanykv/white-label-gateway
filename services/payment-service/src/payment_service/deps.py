"""FastAPI dependencies for payment service."""

from typing import Annotated, AsyncGenerator, Optional
from uuid import UUID

import httpx
from fastapi import HTTPException, Header, status
from sqlalchemy.ext.asyncio import AsyncSession

from shared.database import DatabaseSettings, get_db as shared_get_db, init_db
from payment_service.config import settings


db_settings = DatabaseSettings(database_url=settings.database_url)
init_db(db_settings)  # pragma: no cover - module initialization


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Yield AsyncSession connected to payment_db."""
    async for session in shared_get_db():
        yield session


async def verify_merchant_api_key(
    x_api_key: Annotated[Optional[str], Header(alias="X-API-Key")] = None,
) -> UUID:
    """
    Verify API key and return the associated merchant_id.

    Args:
        x_api_key: API key from X-API-Key header

    Returns:
        Verified merchant_id

    Raises:
        HTTPException: If API key is invalid
    """
    if not x_api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="X-API-Key header is required",
            headers={"WWW-Authenticate": "ApiKey"},
        )

    async with httpx.AsyncClient() as client:
        try:
            headers = {"X-API-Key": x_api_key}
            import logging

            logger = logging.getLogger(__name__)
            logger.info(
                f"Calling merchant-service with X-API-Key header: {x_api_key[:10]}..."
                if x_api_key
                else "No API key provided"
            )
            response = await client.get(
                f"{settings.merchant_service_url}/api/v1/merchants/by-api-key",
                headers=headers,
                timeout=5.0,
            )
            logger.info(f"Merchant-service response status: {response.status_code}")
            if response.status_code == 404:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid API key",
                )
            response.raise_for_status()
            merchant_data = response.json()
            verified_merchant_id = UUID(merchant_data["merchant_id"])

            return verified_merchant_id
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 401 or e.response.status_code == 404:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid API key",
                )
            if e.response.status_code == 422:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid API key format",
                )
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"Merchant service error: {e.response.status_code} - {e.response.text}",
            )
        except httpx.RequestError:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Merchant service unavailable",
            )
