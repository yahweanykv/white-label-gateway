"""Merchant API routes."""

import secrets
from typing import Annotated, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Header, HTTPException, Request, status
from fastapi import Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from merchant_service.deps import get_db, get_current_merchant
from merchant_service.models import Merchant
from merchant_service.schemas import (
    MerchantCreate,
    MerchantResponse,
    MerchantUpdate,
    MerchantByApiKeyResponse,
)



router = APIRouter()


def generate_api_key() -> str:
    """
    Generate a secure API key.

    Returns:
        API key string
    """
    return f"sk_live_{secrets.token_urlsafe(32)}"


@router.post("/", response_model=MerchantResponse, status_code=status.HTTP_201_CREATED)
async def create_merchant(
    merchant_create: MerchantCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """
    Create a new merchant.

    Args:
        merchant_create: Merchant creation data
        db: Database session

    Returns:
        Created merchant
    """
    # Check if domain already exists
    if merchant_create.domain:
        result = await db.execute(
            select(Merchant).where(Merchant.domain == merchant_create.domain)
        )
        existing = result.scalar_one_or_none()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Merchant with domain {merchant_create.domain} already exists",
            )

    # Create new merchant
    api_key = generate_api_key()
    merchant = Merchant(
        name=merchant_create.name,
        domain=merchant_create.domain,
        logo_url=str(merchant_create.logo_url) if merchant_create.logo_url else None,
        primary_color=merchant_create.primary_color,
        background_color=merchant_create.background_color,
        api_keys=[api_key],
        webhook_url=str(merchant_create.webhook_url) if merchant_create.webhook_url else None,
        is_active=True,
    )

    db.add(merchant)
    await db.commit()
    await db.refresh(merchant)

    return MerchantResponse(
        id=merchant.id,
        name=merchant.name,
        domain=merchant.domain,
        logo_url=merchant.logo_url,
        primary_color=merchant.primary_color,
        background_color=merchant.background_color,
        api_keys=merchant.api_keys,
        webhook_url=merchant.webhook_url,
        is_active=merchant.is_active,
        created_at=merchant.created_at,
        updated_at=merchant.updated_at,
    )


@router.get("/me", response_model=MerchantResponse)
async def get_current_merchant_info(
    current_merchant: Annotated[Merchant, Depends(get_current_merchant)],
):
    """
    Get current merchant information.

    Args:
        current_merchant: Current merchant from dependency

    Returns:
        Merchant data
    """
    return MerchantResponse(
        id=current_merchant.id,
        name=current_merchant.name,
        domain=current_merchant.domain,
        logo_url=current_merchant.logo_url,
        primary_color=current_merchant.primary_color,
        background_color=current_merchant.background_color,
        api_keys=current_merchant.api_keys,
        webhook_url=current_merchant.webhook_url,
        is_active=current_merchant.is_active,
        created_at=current_merchant.created_at,
        updated_at=current_merchant.updated_at,
    )


@router.get("/by-api-key", response_model=MerchantByApiKeyResponse)
async def get_merchant_by_api_key(
    db: Annotated[AsyncSession, Depends(get_db)],
    request: Request,
):
    """
    Get merchant by API key (for gateway service).

    Args:
        request: FastAPI request object
        db: Database session

    Returns:
        Merchant data in gateway format
    """
    # Добавить логирование
    from shared.utils.logger import setup_logger
    import os
    logger = setup_logger(__name__, level="INFO", json_logs=os.getenv("JSON_LOGS", "false").lower() == "true")
    
    # Получить заголовок напрямую из request (избегаем проблем с валидацией FastAPI)
    all_headers = dict(request.headers)
    logger.info(f"Received /by-api-key request. Headers keys: {list(all_headers.keys())}")
    
    # Попробовать получить заголовок в разных регистрах
    x_api_key = (
        request.headers.get("X-API-Key") or 
        request.headers.get("x-api-key") or 
        request.headers.get("X-Api-Key")
    )
    
    logger.info(f"X-API-Key from headers: {x_api_key[:20]}..." if x_api_key and len(x_api_key) > 20 else f"X-API-Key: {x_api_key}")
    
    if not x_api_key:
        logger.error("X-API-Key header is missing")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="X-API-Key header is required",
            headers={"WWW-Authenticate": "ApiKey"},
        )
    
    from sqlalchemy import select

    result = await db.execute(
        select(Merchant).where(
            Merchant.api_keys.contains([x_api_key]), Merchant.is_active == True
        )
    )
    merchant = result.scalar_one_or_none()

    if not merchant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Merchant not found",
        )

    # Convert to gateway format
    return MerchantByApiKeyResponse(
        merchant_id=merchant.id,
        name=merchant.name,
        email=f"{merchant.name.lower().replace(' ', '')}@example.com",  # Placeholder email
        status="active" if merchant.is_active else "inactive",
        api_key=x_api_key,
        webhook_url=merchant.webhook_url,
        logo_url=merchant.logo_url,
        primary_color=merchant.primary_color,
        background_color=merchant.background_color,
        created_at=merchant.created_at,
        updated_at=merchant.updated_at,
        metadata=None,
    )


@router.get("/all", response_model=list[MerchantResponse])
async def get_all_merchants(
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """
    Get all merchants.
    
    For demo purposes only - in production this should require authentication.

    Args:
        db: Database session

    Returns:
        List of all merchants
    """
    result = await db.execute(select(Merchant).order_by(Merchant.created_at.desc()))
    merchants = result.scalars().all()
    
    return [
        MerchantResponse(
            id=merchant.id,
            name=merchant.name,
            domain=merchant.domain,
            logo_url=merchant.logo_url,
            primary_color=merchant.primary_color,
            background_color=merchant.background_color,
            api_keys=merchant.api_keys,
            webhook_url=merchant.webhook_url,
            is_active=merchant.is_active,
            created_at=merchant.created_at,
            updated_at=merchant.updated_at,
        )
        for merchant in merchants
    ]


@router.get("/{merchant_id}", response_model=MerchantResponse)
async def get_merchant_by_id(
    merchant_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Fetch merchant by UUID (used by other services)."""
    result = await db.execute(select(Merchant).where(Merchant.id == merchant_id))
    merchant = result.scalar_one_or_none()
    if not merchant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Merchant not found",
        )

    return MerchantResponse(
        id=merchant.id,
        name=merchant.name,
        domain=merchant.domain,
        logo_url=merchant.logo_url,
        primary_color=merchant.primary_color,
        background_color=merchant.background_color,
        api_keys=merchant.api_keys,
        webhook_url=merchant.webhook_url,
        is_active=merchant.is_active,
        created_at=merchant.created_at,
        updated_at=merchant.updated_at,
    )


@router.patch("/me", response_model=MerchantResponse)
async def update_current_merchant(
    merchant_update: MerchantUpdate,
    current_merchant: Annotated[Merchant, Depends(get_current_merchant)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """
    Update current merchant information.

    Args:
        merchant_update: Merchant update data
        current_merchant: Current merchant from dependency
        db: Database session

    Returns:
        Updated merchant data
    """
    # Check domain uniqueness if updating domain
    if merchant_update.domain and merchant_update.domain != current_merchant.domain:
        result = await db.execute(
            select(Merchant).where(
                Merchant.domain == merchant_update.domain, Merchant.id != current_merchant.id
            )
        )
        existing = result.scalar_one_or_none()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Merchant with domain {merchant_update.domain} already exists",
            )

    # Update fields
    update_data = merchant_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        if field in {"logo_url", "webhook_url"} and value:
            setattr(current_merchant, field, str(value))
        elif value is not None:
            setattr(current_merchant, field, value)

    await db.commit()
    await db.refresh(current_merchant)

    return MerchantResponse(
        id=current_merchant.id,
        name=current_merchant.name,
        domain=current_merchant.domain,
        logo_url=current_merchant.logo_url,
        primary_color=current_merchant.primary_color,
        background_color=current_merchant.background_color,
        api_keys=current_merchant.api_keys,
        webhook_url=current_merchant.webhook_url,
        is_active=current_merchant.is_active,
        created_at=current_merchant.created_at,
        updated_at=current_merchant.updated_at,
    )

