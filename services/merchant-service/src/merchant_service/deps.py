"""FastAPI dependencies for merchant service."""

from typing import Annotated, AsyncGenerator, Optional
from uuid import UUID

from fastapi import Depends, HTTPException, Header, status
from sqlalchemy.ext.asyncio import AsyncSession

from shared.database import get_db as shared_get_db, init_db, DatabaseSettings
from merchant_service.config import settings
from merchant_service.models import Merchant


# Initialize database
db_settings = DatabaseSettings(database_url=settings.database_url)
init_db(db_settings)  # pragma: no cover - module initialization


# Use shared get_db directly as dependency
get_db = shared_get_db


async def get_current_merchant(
    x_api_key: Annotated[Optional[str], Header(alias="X-API-Key")] = None,
    db: Annotated[AsyncSession, Depends(get_db)] = None,
) -> Merchant:
    """
    Get current merchant by API key from X-API-Key header.

    Args:
        x_api_key: API key from X-API-Key header
        db: Database session

    Returns:
        Merchant instance

    Raises:
        HTTPException: If API key not provided or merchant not found
    """
    if not x_api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="X-API-Key header is required",
            headers={"WWW-Authenticate": "ApiKey"},
        )

    from sqlalchemy import select

    # Query merchant by API key
    result = await db.execute(
        select(Merchant).where(
            Merchant.api_keys.contains([x_api_key]), Merchant.is_active == True
        )
    )
    merchant = result.scalar_one_or_none()

    if not merchant:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key",
        )

    return merchant

