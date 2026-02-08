"""Mock provider management API routes."""

from typing import Dict
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

from payment_service.config import settings
from payment_service.core.mock_providers import MOCK_PROVIDERS

router = APIRouter()

_current_provider: str = settings.payment_provider


class ProviderResponse(BaseModel):
    """Provider response model."""

    current_provider: str
    available_providers: Dict[str, str]
    environment: str


class ProviderUpdate(BaseModel):
    """Provider update model."""

    provider: str


@router.get("/provider", response_model=ProviderResponse)
async def get_current_provider():
    """
    Get current mock provider.

    Returns:
        Current provider information
    """
    if settings.environment.lower() != "local":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Provider management is only available in local environment",
        )

    available_providers = {
        "mock_success": "Всегда успешный платеж",
        "mock_failed": "Всегда неудачный платеж",
        "mock_3ds": "Требует 3DS аутентификации",
        "mock_slow": "Медленная обработка (processing статус)",
        "mock_random": "Случайный выбор провайдера",
    }

    return ProviderResponse(
        current_provider=_current_provider,
        available_providers=available_providers,
        environment=settings.environment,
    )


@router.put("/provider", response_model=ProviderResponse)
async def update_provider(provider_update: ProviderUpdate):
    """
    Update current mock provider.

    Args:
        provider_update: Provider update data

    Returns:
        Updated provider information
    """
    global _current_provider

    if settings.environment.lower() != "local":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Provider management is only available in local environment",
        )

    provider_name = provider_update.provider.lower()

    if provider_name not in MOCK_PROVIDERS:
        available = ", ".join(MOCK_PROVIDERS.keys())
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unknown provider: {provider_name}. Available providers: {available}",
        )

    _current_provider = provider_name

    available_providers = {
        "mock_success": "Всегда успешный платеж",
        "mock_failed": "Всегда неудачный платеж",
        "mock_3ds": "Требует 3DS аутентификации",
        "mock_slow": "Медленная обработка (processing статус)",
        "mock_random": "Случайный выбор провайдера",
    }

    return ProviderResponse(
        current_provider=_current_provider,
        available_providers=available_providers,
        environment=settings.environment,
    )


def get_current_provider_name() -> str:
    """Get current provider name (for use in payment processing)."""
    global _current_provider
    if settings.environment.lower() == "local" and "mock" in settings.payment_provider.lower():
        return _current_provider
    return settings.payment_provider
