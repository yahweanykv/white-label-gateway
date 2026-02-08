"""Unit tests for shared Redis client."""

from unittest.mock import AsyncMock, MagicMock, patch
import pytest
import json

from shared.redis import RedisClient
from shared.settings import RedisSettings


@pytest.fixture
def redis_settings():
    """Create Redis settings for testing."""
    return RedisSettings(redis_url="redis://localhost:6379")


@pytest.fixture
def redis_client(redis_settings):
    """Create Redis client for testing."""
    return RedisClient(redis_settings)


@pytest.mark.asyncio
async def test_connect(redis_client):
    """Test connecting to Redis."""
    with patch("shared.redis.aioredis.from_url") as mock_from_url:
        mock_redis = AsyncMock()
        mock_from_url.return_value = mock_redis

        await redis_client.connect()

        assert redis_client.client is not None
        mock_from_url.assert_called_once()


@pytest.mark.asyncio
async def test_get_success(redis_client):
    """Test getting value from Redis."""
    mock_redis = AsyncMock()
    mock_redis.get = AsyncMock(return_value="test_value")
    redis_client.client = mock_redis

    result = await redis_client.get("test_key")

    assert result == "test_value"
    mock_redis.get.assert_called_once_with("test_key")


@pytest.mark.asyncio
async def test_get_not_found(redis_client):
    """Test getting non-existent key."""
    mock_redis = AsyncMock()
    mock_redis.get = AsyncMock(return_value=None)
    redis_client.client = mock_redis

    result = await redis_client.get("nonexistent_key")

    assert result is None


@pytest.mark.asyncio
async def test_get_auto_connect(redis_client):
    """Test getting value with auto-connect."""
    with patch("shared.redis.aioredis.from_url") as mock_from_url:
        mock_redis = AsyncMock()
        mock_redis.get = AsyncMock(return_value="value")
        mock_from_url.return_value = mock_redis

        result = await redis_client.get("test_key")

        assert result == "value"
        assert redis_client.client is not None


@pytest.mark.asyncio
async def test_set_string(redis_client):
    """Test setting string value."""
    mock_redis = AsyncMock()
    mock_redis.set = AsyncMock(return_value=True)
    redis_client.client = mock_redis

    result = await redis_client.set("test_key", "test_value")

    assert result is True
    mock_redis.set.assert_called_once_with("test_key", "test_value", ex=None, nx=False)


@pytest.mark.asyncio
async def test_set_dict(redis_client):
    """Test setting dict value (should be JSON serialized)."""
    mock_redis = AsyncMock()
    mock_redis.set = AsyncMock(return_value=True)
    redis_client.client = mock_redis

    value = {"key": "value"}
    result = await redis_client.set("test_key", value)

    assert result is True
    mock_redis.set.assert_called_once_with("test_key", json.dumps(value), ex=None, nx=False)


@pytest.mark.asyncio
async def test_set_with_expiration(redis_client):
    """Test setting value with expiration."""
    mock_redis = AsyncMock()
    mock_redis.set = AsyncMock(return_value=True)
    redis_client.client = mock_redis

    result = await redis_client.set("test_key", "test_value", ex=60)

    assert result is True
    mock_redis.set.assert_called_once_with("test_key", "test_value", ex=60, nx=False)


@pytest.mark.asyncio
async def test_set_with_nx(redis_client):
    """Test setting value with nx flag."""
    mock_redis = AsyncMock()
    mock_redis.set = AsyncMock(return_value=True)
    redis_client.client = mock_redis

    result = await redis_client.set("test_key", "test_value", nx=True)

    assert result is True
    mock_redis.set.assert_called_once_with("test_key", "test_value", ex=None, nx=True)


@pytest.mark.asyncio
async def test_delete(redis_client):
    """Test deleting keys."""
    mock_redis = AsyncMock()
    mock_redis.delete = AsyncMock(return_value=2)
    redis_client.client = mock_redis

    result = await redis_client.delete("key1", "key2")

    assert result == 2
    mock_redis.delete.assert_called_once_with("key1", "key2")


@pytest.mark.asyncio
async def test_exists(redis_client):
    """Test checking if keys exist."""
    mock_redis = AsyncMock()
    mock_redis.exists = AsyncMock(return_value=1)
    redis_client.client = mock_redis

    result = await redis_client.exists("test_key")

    assert result == 1
    mock_redis.exists.assert_called_once_with("test_key")


@pytest.mark.asyncio
async def test_expire(redis_client):
    """Test setting expiration for key."""
    mock_redis = AsyncMock()
    mock_redis.expire = AsyncMock(return_value=True)
    redis_client.client = mock_redis

    result = await redis_client.expire("test_key", 60)

    assert result is True
    mock_redis.expire.assert_called_once_with("test_key", 60)


@pytest.mark.asyncio
async def test_get_json(redis_client):
    """Test getting and deserializing JSON value."""
    mock_redis = AsyncMock()
    mock_redis.get = AsyncMock(return_value='{"key": "value"}')
    redis_client.client = mock_redis

    result = await redis_client.get_json("test_key")

    assert result == {"key": "value"}


@pytest.mark.asyncio
async def test_get_json_not_found(redis_client):
    """Test getting JSON value that doesn't exist."""
    mock_redis = AsyncMock()
    mock_redis.get = AsyncMock(return_value=None)
    redis_client.client = mock_redis

    result = await redis_client.get_json("nonexistent_key")

    assert result is None


@pytest.mark.asyncio
async def test_set_json(redis_client):
    """Test serializing and setting JSON value."""
    mock_redis = AsyncMock()
    mock_redis.set = AsyncMock(return_value=True)
    redis_client.client = mock_redis

    value = {"key": "value"}
    result = await redis_client.set_json("test_key", value)

    assert result is True
    mock_redis.set.assert_called_once_with("test_key", json.dumps(value), ex=None, nx=False)


@pytest.mark.asyncio
async def test_make_key(redis_client):
    """Test creating Redis key with prefix."""
    key = redis_client.make_key("payment", "123")
    assert key.startswith("payment_gateway:")
    assert "payment" in key
    assert "123" in key


@pytest.mark.asyncio
async def test_make_key_with_tenant(redis_client):
    """Test creating Redis key with tenant ID."""
    from uuid import uuid4

    tenant_id = uuid4()
    key = redis_client.make_key("payment", "123", tenant_id=tenant_id)
    assert f"tenant:{tenant_id}" in key


@pytest.mark.asyncio
async def test_health_check_success(redis_client):
    """Test health check when Redis is healthy."""
    mock_redis = AsyncMock()
    mock_redis.ping = AsyncMock(return_value=True)
    redis_client.client = mock_redis

    result = await redis_client.health_check()

    assert result is True
    mock_redis.ping.assert_called_once()


@pytest.mark.asyncio
async def test_health_check_failure(redis_client):
    """Test health check when Redis connection fails."""
    with patch("shared.redis.aioredis.from_url") as mock_from_url:
        mock_redis = AsyncMock()
        mock_redis.ping = AsyncMock(side_effect=Exception("Connection failed"))
        mock_from_url.return_value = mock_redis

        result = await redis_client.health_check()

        assert result is False


@pytest.mark.asyncio
async def test_disconnect(redis_client):
    """Test disconnecting from Redis."""
    mock_redis = AsyncMock()
    mock_redis.close = AsyncMock()
    redis_client.client = mock_redis

    await redis_client.disconnect()

    assert redis_client.client is None
    mock_redis.close.assert_called_once()
