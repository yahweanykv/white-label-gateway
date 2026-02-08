"""Pytest configuration and shared fixtures."""

import os
import sys
from pathlib import Path
from typing import AsyncGenerator
from uuid import uuid4

import pytest
from httpx import AsyncClient
from testcontainers.postgres import PostgresContainer
from testcontainers.redis import RedisContainer

# Add service paths to sys.path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "services" / "gateway" / "src"))
sys.path.insert(0, str(project_root / "services" / "merchant-service" / "src"))
sys.path.insert(0, str(project_root / "services" / "payment-service" / "src"))
sys.path.insert(0, str(project_root / "services" / "notification-service" / "src"))
sys.path.insert(0, str(project_root / "services" / "fraud-service" / "src"))
sys.path.insert(0, str(project_root / "shared" / "src"))

# Set test environment variables
os.environ["ENVIRONMENT"] = "test"
os.environ["LOG_LEVEL"] = "DEBUG"


@pytest.fixture(scope="session")
def postgres_container():
    """PostgreSQL testcontainer fixture."""
    with PostgresContainer("postgres:16", driver="psycopg2") as postgres:
        yield postgres


@pytest.fixture(scope="session")
def redis_container():
    """Redis testcontainer fixture."""
    with RedisContainer("redis:7") as redis:
        yield redis


@pytest.fixture
def test_database_url(postgres_container):
    """Get test database URL."""
    return postgres_container.get_connection_url().replace("psycopg2", "asyncpg")


@pytest.fixture
def test_redis_url(redis_container):
    """Get test Redis URL."""
    host = redis_container.get_container_host_ip()
    port = redis_container.get_exposed_port(6379)
    return f"redis://{host}:{port}"


@pytest.fixture
def random_merchant_id():
    """Generate random merchant ID."""
    return uuid4()


@pytest.fixture
def random_payment_id():
    """Generate random payment ID."""
    return uuid4()

