"""API routes."""

from fastapi import APIRouter

from payment_service.api import payments, providers

router = APIRouter()

router.include_router(payments.router, prefix="/payments", tags=["payments"])
router.include_router(providers.router, tags=["providers"])

