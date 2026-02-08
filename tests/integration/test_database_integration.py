"""Integration tests for database operations."""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from merchant_service.models import Merchant
from shared.database import Base


@pytest.mark.asyncio
async def test_merchant_crud_operations(postgres_container):
    """Test CRUD operations for merchants."""
    # Get connection URL and convert to asyncpg
    db_url = postgres_container.get_connection_url().replace("psycopg2", "asyncpg")

    engine = create_async_engine(db_url, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        # Create merchant
        merchant = Merchant(
            name="Integration Test Merchant",
            domain="integration.test",
            api_keys=["sk_test_integration"],
            is_active=True,
        )
        session.add(merchant)
        await session.commit()
        await session.refresh(merchant)

        merchant_id = merchant.id
        assert merchant_id is not None
        assert merchant.name == "Integration Test Merchant"

        # Read merchant
        from sqlalchemy import select

        result = await session.execute(select(Merchant).where(Merchant.id == merchant_id))
        retrieved = result.scalar_one()
        assert retrieved.name == "Integration Test Merchant"

        # Update merchant
        retrieved.name = "Updated Merchant"
        await session.commit()
        await session.refresh(retrieved)
        assert retrieved.name == "Updated Merchant"

        # Delete merchant
        await session.delete(retrieved)
        await session.commit()

        # Verify deletion
        result = await session.execute(select(Merchant).where(Merchant.id == merchant_id))
        assert result.scalar_one_or_none() is None

    await engine.dispose()


@pytest.mark.asyncio
async def test_merchant_api_key_lookup(postgres_container):
    """Test merchant lookup by API key."""
    db_url = postgres_container.get_connection_url().replace("psycopg2", "asyncpg")

    engine = create_async_engine(db_url, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        api_key = "sk_test_lookup_123"
        merchant = Merchant(
            name="Lookup Test Merchant",
            domain="lookup.test",
            api_keys=[api_key, "sk_test_secondary"],
            is_active=True,
        )
        session.add(merchant)
        await session.commit()

        # Lookup by API key
        from sqlalchemy import select

        result = await session.execute(
            select(Merchant).where(Merchant.api_keys.contains([api_key]))
        )
        found = result.scalar_one_or_none()
        assert found is not None
        assert found.name == "Lookup Test Merchant"
        assert api_key in found.api_keys

    await engine.dispose()


@pytest.mark.asyncio
async def test_merchant_domain_uniqueness(postgres_container):
    """Test merchant domain uniqueness constraint."""
    db_url = postgres_container.get_connection_url().replace("psycopg2", "asyncpg")

    engine = create_async_engine(db_url, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        # Create first merchant
        merchant1 = Merchant(
            name="First Merchant",
            domain="unique.test",
            api_keys=["sk_test_1"],
            is_active=True,
        )
        session.add(merchant1)
        await session.commit()

        # Try to create second merchant with same domain
        merchant2 = Merchant(
            name="Second Merchant",
            domain="unique.test",
            api_keys=["sk_test_2"],
            is_active=True,
        )
        session.add(merchant2)

        # Should raise integrity error
        from sqlalchemy.exc import IntegrityError

        with pytest.raises(IntegrityError):
            await session.commit()

    await engine.dispose()

