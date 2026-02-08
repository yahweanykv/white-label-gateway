"""Mock payment providers for local development."""

from __future__ import annotations

import asyncio
import random
from datetime import datetime
from typing import Dict, Optional
from uuid import UUID, uuid4

from shared.models.payment import PaymentRequest, PaymentResponse, PaymentStatus


class PaymentStore:
    """In-memory payment storage for mock providers."""

    def __init__(self) -> None:
        self._payments: Dict[UUID, PaymentResponse] = {}
        self._lock = asyncio.Lock()

    async def save(self, payment: PaymentResponse) -> PaymentResponse:
        """Persist payment state."""
        async with self._lock:
            self._payments[payment.payment_id] = payment
            return payment

    async def get(self, payment_id: UUID) -> Optional[PaymentResponse]:
        """Return payment by ID."""
        async with self._lock:
            payment = self._payments.get(payment_id)
            return payment.model_copy(deep=True) if payment else None

    async def update(
        self,
        payment_id: UUID,
        *,
        status: Optional[PaymentStatus] = None,
        requires_action: Optional[bool] = None,
        next_action: Optional[dict] = None,
        next_action_url: Optional[str] = None,
        error_message: Optional[str] = None,
        metadata: Optional[dict] = None,
    ) -> Optional[PaymentResponse]:
        """Update payment state."""
        async with self._lock:
            payment = self._payments.get(payment_id)
            if not payment:
                return None

            update_data = payment.model_dump()
            update_data["updated_at"] = datetime.utcnow()
            if status:
                update_data["status"] = status
            if requires_action is not None:
                update_data["requires_action"] = requires_action
            if next_action is not None:
                update_data["next_action"] = next_action
            if next_action_url is not None:
                update_data["next_action_url"] = next_action_url
            if error_message is not None:
                update_data["error_message"] = error_message
            if metadata is not None:
                update_data["metadata"] = metadata

            updated = PaymentResponse(**update_data)
            self._payments[payment_id] = updated
            return updated


payment_store = PaymentStore()


class BaseMockProvider:
    """Base class for mock providers."""

    def __init__(self, store: PaymentStore) -> None:
        self.store = store

    def _make_base_payment(
        self,
        request: PaymentRequest,
        *,
        status: PaymentStatus,
        requires_action: bool = False,
        next_action: Optional[dict] = None,
        metadata: Optional[dict] = None,
        transaction_id: Optional[str] = None,
        error_message: Optional[str] = None,
    ) -> PaymentResponse:
        now = datetime.utcnow()
        return PaymentResponse(
            payment_id=uuid4(),
            merchant_id=request.merchant_id,
            amount=request.amount,
            currency=request.currency,
            status=status,
            payment_method=request.payment_method,
            created_at=now,
            updated_at=now,
            transaction_id=transaction_id,
            error_message=error_message,
            requires_action=requires_action,
            next_action=next_action,
            metadata=metadata,
        )

    async def _persist(self, payment: PaymentResponse) -> PaymentResponse:
        return await self.store.save(payment)

    async def process(self, request: PaymentRequest) -> PaymentResponse:
        raise NotImplementedError


class SuccessMockProvider(BaseMockProvider):
    """Always succeeds."""

    async def process(self, request: PaymentRequest) -> PaymentResponse:
        payment = self._make_base_payment(
            request,
            status=PaymentStatus.SUCCEEDED,
            transaction_id=f"txn_{uuid4().hex[:10]}",
        )
        return await self._persist(payment)


class FailedMockProvider(BaseMockProvider):
    """Always fails."""

    async def process(self, request: PaymentRequest) -> PaymentResponse:
        payment = self._make_base_payment(
            request,
            status=PaymentStatus.FAILED,
            error_message="Mocked decline: insufficient funds",
        )
        return await self._persist(payment)


class ThreeDSMockProvider(BaseMockProvider):
    """Requires 3-D Secure confirmation."""

    async def process(self, request: PaymentRequest) -> PaymentResponse:
        payment = self._make_base_payment(
            request,
            status=PaymentStatus.REQUIRES_ACTION,
            requires_action=True,
            next_action={
                "type": "redirect",
                "path": "/mock-3ds",
                "payment_id": None,  # substituted later
            },
        )
        stored = await self._persist(payment)
        # Update next_action with actual payment_id
        await self.store.update(
            stored.payment_id,
            next_action={
                "type": "redirect",
                "path": "/mock-3ds",
                "payment_id": str(stored.payment_id),
            },
        )
        refreshed = await self.store.get(stored.payment_id)
        return refreshed or stored


class RandomMockProvider(BaseMockProvider):
    """Randomly picks another provider result."""

    def __init__(self, store: PaymentStore, providers: Dict[str, BaseMockProvider]) -> None:
        super().__init__(store)
        self.providers = providers

    async def process(self, request: PaymentRequest) -> PaymentResponse:
        candidates = [name for name in self.providers if name != "mock_random"]
        choice = random.choice(candidates)
        return await self.providers[choice].process(request)


class SlowMockProvider(BaseMockProvider):
    """Simulates slow processing."""

    async def process(self, request: PaymentRequest) -> PaymentResponse:
        payment = self._make_base_payment(
            request,
            status=PaymentStatus.PROCESSING,
            metadata={"expected_settlement_seconds": 10},
        )
        return await self._persist(payment)


def build_mock_providers(store: PaymentStore) -> Dict[str, BaseMockProvider]:
    """Factory for provider registry."""
    base_providers: Dict[str, BaseMockProvider] = {
        "mock_success": SuccessMockProvider(store),
        "mock_failed": FailedMockProvider(store),
        "mock_3ds": ThreeDSMockProvider(store),
        "mock_slow": SlowMockProvider(store),
    }
    base_providers["mock_random"] = RandomMockProvider(store, base_providers)
    return base_providers


MOCK_PROVIDERS = build_mock_providers(payment_store)


def get_provider(name: str) -> BaseMockProvider:
    """Return provider by name."""
    normalized = name.lower()
    return MOCK_PROVIDERS.get(normalized, MOCK_PROVIDERS["mock_success"])
