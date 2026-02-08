"""API routes."""

from fastapi import APIRouter

from merchant_service.api import merchants, dashboard

router = APIRouter()

router.include_router(merchants.router, prefix="/merchants", tags=["merchants"])
router.include_router(dashboard.router, tags=["dashboard"])
