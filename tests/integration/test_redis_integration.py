"""Integration tests for Redis operations."""

import pytest
from redis import Redis


@pytest.mark.asyncio
async def test_redis_connection(redis_container):
    """Test basic Redis connection."""
    # Get host and port from container
    host = redis_container.get_container_host_ip()
    port = redis_container.get_exposed_port(6379)
    # Parse URL to get host and port
    import redis.asyncio as aioredis

    redis_client = aioredis.from_url(
        f"redis://{host}:{port}", decode_responses=True
    )

    # Test basic operations
    await redis_client.set("test_key", "test_value")
    value = await redis_client.get("test_key")
    assert value == "test_value"

    await redis_client.delete("test_key")
    value = await redis_client.get("test_key")
    assert value is None

    await redis_client.close()


@pytest.mark.asyncio
async def test_redis_rate_limiting(redis_container):
    """Test rate limiting with Redis."""
    import redis.asyncio as aioredis

    # Get host and port from container
    host = redis_container.get_container_host_ip()
    port = redis_container.get_exposed_port(6379)
    redis_client = aioredis.from_url(
        f"redis://{host}:{port}", decode_responses=True
    )

    # Simulate rate limiting
    key = "rate_limit:merchant_123"
    limit = 10
    window = 60

    # Increment counter
    current = await redis_client.incr(key)
    await redis_client.expire(key, window)

    assert current == 1

    # Increment multiple times
    for _ in range(5):
        current = await redis_client.incr(key)

    final_count = await redis_client.get(key)
    assert int(final_count) == 6

    await redis_client.delete(key)
    await redis_client.close()

