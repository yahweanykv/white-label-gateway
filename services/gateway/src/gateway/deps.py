"""FastAPI dependencies."""

import hashlib
from typing import Annotated, AsyncGenerator, Optional
from uuid import UUID

import httpx
from fastapi import Depends, HTTPException, Header, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from shared.database import get_db as shared_get_db, init_db, DatabaseSettings
from shared.redis import get_redis as shared_get_redis, init_redis, RedisSettings
from shared.models.merchant import Merchant
from gateway.config import settings

# Cache TTL for merchant lookup (seconds)
MERCHANT_CACHE_TTL = 60

# Initialize database and redis
db_settings = DatabaseSettings(database_url=settings.database_url)
redis_settings = RedisSettings(redis_url=settings.redis_url)

init_db(db_settings)  # pragma: no cover - module initialization
init_redis(redis_settings)  # pragma: no cover - module initialization


async def get_db(
    tenant_id: Optional[UUID] = None,
) -> AsyncGenerator[AsyncSession, None]:
    """
    Get database session dependency.

    Args:
        tenant_id: Optional tenant ID from request context

    Yields:
        AsyncSession: Database session
    """
    async for session in shared_get_db(tenant_id=tenant_id):
        yield session


def get_redis():
    """
    Get Redis client dependency.

    Returns:
        RedisClient instance
    """
    return shared_get_redis()


async def get_current_merchant(
    request: Request,
    x_api_key: Annotated[Optional[str], Header(alias="X-API-Key")] = None,
) -> Merchant:
    """
    Get current merchant by API key from X-API-Key header.
    Uses Redis cache to reduce calls to merchant service.
    """
    if not x_api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="X-API-Key header is required",
            headers={"WWW-Authenticate": "ApiKey"},
        )

    from shared.utils.logger import setup_logger
    import os
    logger = setup_logger(__name__, level="INFO", json_logs=os.getenv("JSON_LOGS", "false").lower() == "true")

    # Try cache first (Redis)
    api_key_hash = hashlib.sha256(x_api_key.encode()).hexdigest()[:16]
    cache_key = f"merchant_cache:{api_key_hash}"
    redis = get_redis()
    try:
        await redis.connect()
        cached = await redis.get_json(cache_key)
        if cached:
            merchant = Merchant(**cached)
            if merchant.status != "active":
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Merchant status is {merchant.status}",
                )
            request.state.merchant_id = merchant.merchant_id
            request.state.tenant_id = merchant.merchant_id
            request.state.api_key = x_api_key
            return merchant
    except Exception:
        pass  # Cache miss or error — fall through to merchant service

    # Cache miss — fetch from merchant service
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
            merchant = Merchant(**merchant_data)

            if merchant.status != "active":
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Merchant status is {merchant.status}",
                )

            # Store in cache
            try:
                await redis.set_json(cache_key, merchant_data, ex=MERCHANT_CACHE_TTL)
            except Exception:
                pass

            request.state.merchant_id = merchant.merchant_id
            request.state.tenant_id = merchant.merchant_id
            request.state.api_key = x_api_key
            return merchant
        except httpx.HTTPStatusError as e:
            if e.response.status_code in (401, 404):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid API key",
                )
            logger.error(f"Merchant service error: {e.response.status_code} - {e.response.text}")
            if e.response.status_code == 422:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid API key or missing X-API-Key header",
                )
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"Merchant service error: {e.response.status_code}",
            )
        except httpx.RequestError as e:
            logger.error(f"Merchant service unavailable: {type(e).__name__}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Merchant service unavailable",
            )

