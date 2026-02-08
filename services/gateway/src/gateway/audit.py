"""Helpers for persisting gateway payment audit logs to PostgreSQL."""

from __future__ import annotations

from typing import Any, Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from shared.database import db
from shared.models.db import GatewayPaymentLog


async def _with_session(tenant_id: Optional[UUID], func):
    if db is None:  # pragma: no cover - initialization guard
        # Database not initialized - skip audit logging
        # This can happen if database is not configured or not available
        return None
    async with db.get_session(tenant_id=None) as session:
        return await func(session)


async def create_payment_log(
    *,
    merchant_id: UUID,
    path: str,
    method: str,
    request_payload: dict[str, Any],
) -> UUID:
    """Persist initial gateway payment request metadata."""
    from uuid import uuid4

    async def _create(session: AsyncSession):
        entry = GatewayPaymentLog(
            merchant_id=merchant_id,
            path=path,
            method=method,
            request_payload=request_payload,
        )
        session.add(entry)
        await session.flush()
        return entry.request_id

    result = await _with_session(merchant_id, _create)
    # If database is not available, return a dummy UUID
    if result is None:
        return uuid4()
    return result


async def finalize_payment_log(
    *,
    merchant_id: UUID,
    request_id: UUID,
    status_code: Optional[int],
    response_payload: Optional[dict[str, Any]],
    error_message: Optional[str] = None,
    payment_id: Optional[UUID] = None,
) -> None:
    """Update gateway payment request audit log with response metadata."""

    async def _update(session: AsyncSession):
        entry = await session.get(GatewayPaymentLog, request_id)
        if not entry:
            # Attempt lookup within tenant context if row-level security duplicates
            result = await session.execute(
                select(GatewayPaymentLog).where(GatewayPaymentLog.request_id == request_id)
            )
            entry = result.scalar_one_or_none()
        if not entry:
            return
        entry.mark_response(
            status_code=status_code,
            response_payload=response_payload,
            error_message=error_message,
            payment_id=payment_id,
        )

    # Skip if database is not available
    result = await _with_session(merchant_id, _update)
    if result is None:
        return
