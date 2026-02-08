"""API routes."""

from fastapi import APIRouter

from notification_service.api import notifications

router = APIRouter()

router.include_router(notifications.router, prefix="/notifications", tags=["notifications"])
