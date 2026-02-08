"""API routes."""

from fastapi import APIRouter

from gateway.api import payments, merchants

router = APIRouter()

router.include_router(payments.router, prefix="/payments", tags=["payments"])
router.include_router(merchants.router, prefix="/merchants", tags=["merchants"])

