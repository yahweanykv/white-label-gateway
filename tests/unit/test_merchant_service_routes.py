"""Unit tests for merchant service routes."""

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from merchant_service.api.merchants import router
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
    from merchant_service.deps import get_db

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    return TestClient(app)


class TestMerchantServiceRoutes:
    """Tests for merchant service routes."""

    @pytest.mark.asyncio
    async def test_create_merchant_success(self, client):
        """Test successful merchant creation."""
        merchant_data = {
            "name": "Test Merchant",
            "domain": "test.example.com",
            "logo_url": "https://example.com/logo.png",
            "primary_color": "#FF0000",
            "background_color": "#FFFFFF",
        }

        response = client.post("/api/v1/merchants", json=merchant_data)
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Test Merchant"
        assert data["domain"] == "test.example.com"
        assert len(data["api_keys"]) > 0
        assert data["api_keys"][0].startswith("sk_live_")

    @pytest.mark.asyncio
    async def test_create_merchant_duplicate_domain(self, client):
        """Test creating merchant with duplicate domain."""
        merchant_data = {
            "name": "First Merchant",
            "domain": "duplicate.example.com",
        }

        response1 = client.post("/api/v1/merchants", json=merchant_data)
        assert response1.status_code == 201

        merchant_data["name"] = "Second Merchant"
        response2 = client.post("/api/v1/merchants", json=merchant_data)
        assert response2.status_code == 409
        assert "already exists" in response2.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_get_merchant_by_api_key(self, client):
        """Test getting merchant by API key."""
        merchant_data = {
            "name": "API Key Merchant",
            "domain": "apikey.example.com",
        }
        create_response = client.post("/api/v1/merchants", json=merchant_data)
        assert create_response.status_code == 201
        api_key = create_response.json()["api_keys"][0]

        response = client.get("/api/v1/merchants/by-api-key", headers={"X-API-Key": api_key})
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "API Key Merchant"
        assert data["api_key"] == api_key

    @pytest.mark.asyncio
    async def test_get_merchant_by_api_key_not_found(self, client):
        """Test getting merchant with invalid API key."""
        response = client.get("/api/v1/merchants/by-api-key", headers={"X-API-Key": "invalid_key"})
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_get_merchant_by_id_success(self, client):
        """Test getting merchant by ID."""
        merchant_data = {
            "name": "Get By ID Merchant",
            "domain": "getbyid.example.com",
        }
        create_response = client.post("/api/v1/merchants", json=merchant_data)
        assert create_response.status_code == 201
        merchant_id = create_response.json()["id"]

        response = client.get(f"/api/v1/merchants/{merchant_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == merchant_id
        assert data["name"] == "Get By ID Merchant"

    @pytest.mark.asyncio
    async def test_get_merchant_by_id_not_found(self, client):
        """Test getting non-existent merchant by ID."""
        from uuid import uuid4

        merchant_id = uuid4()
        response = client.get(f"/api/v1/merchants/{merchant_id}")
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_update_merchant_success(self, client):
        """Test updating merchant."""
        merchant_data = {
            "name": "Update Test Merchant",
            "domain": "updatetest.example.com",
        }
        create_response = client.post("/api/v1/merchants", json=merchant_data)
        assert create_response.status_code == 201
        api_key = create_response.json()["api_keys"][0]

        update_data = {
            "name": "Updated Merchant Name",
            "primary_color": "#FF0000",
        }
        response = client.patch(
            "/api/v1/merchants/me", json=update_data, headers={"X-API-Key": api_key}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Updated Merchant Name"
        assert data["primary_color"] == "#FF0000"

    @pytest.mark.asyncio
    async def test_update_merchant_duplicate_domain(self, client):
        """Test updating merchant with duplicate domain."""
        merchant1_data = {
            "name": "First Merchant",
            "domain": "first.example.com",
        }
        merchant2_data = {
            "name": "Second Merchant",
            "domain": "second.example.com",
        }
        create1_response = client.post("/api/v1/merchants", json=merchant1_data)
        create2_response = client.post("/api/v1/merchants", json=merchant2_data)
        assert create1_response.status_code == 201
        assert create2_response.status_code == 201
        api_key2 = create2_response.json()["api_keys"][0]

        update_data = {
            "domain": "first.example.com",
        }
        response = client.patch(
            "/api/v1/merchants/me", json=update_data, headers={"X-API-Key": api_key2}
        )
        assert response.status_code == 409

    @pytest.mark.asyncio
    async def test_get_current_merchant_info(self, client):
        """Test getting current merchant info."""
        merchant_data = {
            "name": "Current Merchant",
            "domain": "current.example.com",
        }
        create_response = client.post("/api/v1/merchants", json=merchant_data)
        assert create_response.status_code == 201
        api_key = create_response.json()["api_keys"][0]

        response = client.get("/api/v1/merchants/me", headers={"X-API-Key": api_key})
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Current Merchant"

    @pytest.mark.asyncio
    async def test_create_merchant_without_domain(self, client):
        """Test creating merchant without domain."""
        merchant_data = {
            "name": "No Domain Merchant",
        }

        response = client.post("/api/v1/merchants", json=merchant_data)
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "No Domain Merchant"
        assert data["domain"] is None

    @pytest.mark.asyncio
    async def test_create_merchant_with_optional_fields(self, client):
        """Test creating merchant with all optional fields."""
        merchant_data = {
            "name": "Full Merchant",
            "domain": "full.example.com",
            "logo_url": "https://example.com/logo.png",
            "primary_color": "#FF0000",
            "background_color": "#FFFFFF",
            "webhook_url": "https://example.com/webhook",
        }

        response = client.post("/api/v1/merchants", json=merchant_data)
        assert response.status_code == 201
        data = response.json()
        assert data["logo_url"] == "https://example.com/logo.png"
        assert data["primary_color"] == "#FF0000"
        assert data["webhook_url"] == "https://example.com/webhook"

    @pytest.mark.asyncio
    async def test_update_merchant_partial(self, client):
        """Test partial update of merchant."""
        merchant_data = {
            "name": "Partial Update Merchant",
            "domain": "partial.example.com",
        }
        create_response = client.post("/api/v1/merchants", json=merchant_data)
        assert create_response.status_code == 201
        api_key = create_response.json()["api_keys"][0]

        update_data = {
            "name": "Updated Name Only",
        }
        response = client.patch(
            "/api/v1/merchants/me", json=update_data, headers={"X-API-Key": api_key}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Updated Name Only"
        assert data["domain"] == "partial.example.com"  # Should remain unchanged

    @pytest.mark.asyncio
    async def test_update_merchant_same_domain(self, client):
        """Test updating merchant with same domain (should succeed)."""
        # Create merchant first
        merchant_data = {
            "name": "Same Domain Merchant",
            "domain": "samedomain.example.com",
        }
        create_response = client.post("/api/v1/merchants", json=merchant_data)
        assert create_response.status_code == 201
        api_key = create_response.json()["api_keys"][0]

        update_data = {
            "domain": "samedomain.example.com",
        }
        response = client.patch(
            "/api/v1/merchants/me", json=update_data, headers={"X-API-Key": api_key}
        )
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_get_merchant_by_api_key_inactive(self, client):
        """Test getting inactive merchant by API key."""
        merchant_data = {
            "name": "Inactive API Key Merchant",
            "domain": "inactiveapikey.example.com",
        }
        create_response = client.post("/api/v1/merchants", json=merchant_data)
        assert create_response.status_code == 201
        api_key = create_response.json()["api_keys"][0]

        response = client.get("/api/v1/merchants/by-api-key", headers={"X-API-Key": api_key})
        assert response.status_code == 200
