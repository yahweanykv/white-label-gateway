"""API routes."""

from fastapi import APIRouter

from fraud_service.api import fraud

router = APIRouter()

router.include_router(fraud.router, prefix="/fraud", tags=["fraud"])

