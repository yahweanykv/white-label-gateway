"""Extended unit tests for merchant service merchants routes."""

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from merchant_service.api.merchants import generate_api_key, router
from merchant_service.models import Merchant
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from shared.database import Base


@pytest.fixture(scope="function")
async def db_session():
    """Create test database session."""
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    session = async_session()
    yield session
    await session.rollback()
    await session.close()
    await engine.dispose()


@pytest.fixture
def app():
    """Create test FastAPI app."""
    app = FastAPI()
    app.include_router(router, prefix="/api/v1/merchants")
    return app


@pytest.fixture
def client(app, db_session):
    """Create test client with database dependency override."""
    from merchant_service.deps import get_current_merchant, get_db

    async def override_get_db():
        yield db_session

    async def override_get_current_merchant(x_api_key: str = None):
        if not x_api_key:
            from fastapi import HTTPException, status

            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="X-API-Key header is required",
            )
        result = await db_session.execute(
            __import__("sqlalchemy")
            .select(Merchant)
            .where(Merchant.api_keys.contains([x_api_key]), Merchant.is_active.is_(True))
        )
        merchant = result.scalar_one_or_none()
        if not merchant:
            from fastapi import HTTPException, status

            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid API key",
            )
        return merchant

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_merchant] = override_get_current_merchant
    return TestClient(app)


class TestMerchantServiceMerchantsExtended:
    """Extended tests for merchant service routes."""

    def test_generate_api_key(self):
        """Test API key generation."""
        key1 = generate_api_key()
        key2 = generate_api_key()

        assert key1.startswith("sk_live_")
        assert key2.startswith("sk_live_")
        assert key1 != key2  # Should be different
        assert len(key1) > 20  # Should be reasonably long

    @pytest.mark.asyncio
    async def test_create_merchant_with_none_domain(self, client):
        """Test creating merchant with None domain."""
        merchant_data = {
            "name": "No Domain Merchant",
            "domain": None,
        }

        response = client.post("/api/v1/merchants", json=merchant_data)
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "No Domain Merchant"
        assert data["domain"] is None

    @pytest.mark.asyncio
    async def test_update_merchant_with_url_fields(self, client):
        """Test updating merchant with URL fields."""
        # Create merchant first
        merchant_data = {
            "name": "URL Test Merchant",
            "domain": "urltest.example.com",
        }
        create_response = client.post("/api/v1/merchants", json=merchant_data)
        assert create_response.status_code == 201
        api_key = create_response.json()["api_keys"][0]

        # Update with URL fields
        update_data = {
            "logo_url": "https://example.com/new-logo.png",
            "webhook_url": "https://example.com/webhook",
        }
        response = client.patch(
            "/api/v1/merchants/me", json=update_data, headers={"X-API-Key": api_key}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["logo_url"] == "https://example.com/new-logo.png"
        assert data["webhook_url"] == "https://example.com/webhook"

    @pytest.mark.asyncio
    async def test_update_merchant_with_none_values(self, client):
        """Test updating merchant with None values."""
        # Create merchant first
        merchant_data = {
            "name": "None Test Merchant",
            "domain": "nonetest.example.com",
            "primary_color": "#FF0000",
        }
        create_response = client.post("/api/v1/merchants", json=merchant_data)
        assert create_response.status_code == 201
        api_key = create_response.json()["api_keys"][0]

        # Update with None value (should be ignored)
        update_data = {
            "primary_color": None,
        }
        response = client.patch(
            "/api/v1/merchants/me", json=update_data, headers={"X-API-Key": api_key}
        )
        assert response.status_code == 200
        # None values should not update the field
        data = response.json()
        assert data["primary_color"] == "#FF0000"  # Should remain unchanged

    @pytest.mark.asyncio
    async def test_get_merchant_by_api_key_inactive(self, client):
        """Test getting inactive merchant by API key (should fail)."""
        # Create merchant first
        merchant_data = {
            "name": "Inactive API Key Merchant",
            "domain": "inactiveapikey.example.com",
        }
        create_response = client.post("/api/v1/merchants", json=merchant_data)
        assert create_response.status_code == 201
        api_key = create_response.json()["api_keys"][0]
        merchant_id = create_response.json()["id"]

        # Deactivate merchant
        from sqlalchemy import select

        result = await client.app.dependency_overrides[
            __import__("merchant_service.deps").get_db
        ]().__anext__()
        merchant = await result.execute(select(Merchant).where(Merchant.id == merchant_id))
        merchant_obj = merchant.scalar_one()
        merchant_obj.is_active = False
        await result.commit()

        # Try to get by API key (should fail)
        response = client.get("/api/v1/merchants/by-api-key", headers={"X-API-Key": api_key})
        assert response.status_code == 404
