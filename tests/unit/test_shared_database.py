"""Unit tests for shared database module."""

from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from shared.database import Database, Base, init_db, get_db, db
from shared.settings import DatabaseSettings


def test_base_tablename():
    """Test Base class table name generation."""

    class TestModel(Base):
        pass

    assert TestModel.__tablename__ == "testmodels"


@pytest.fixture
def db_settings():
    """Create database settings for testing."""
    return DatabaseSettings(database_url="postgresql+asyncpg://user:pass@localhost:5432/testdb")


@pytest.fixture
def database(db_settings):
    """Create database instance for testing."""
    return Database(db_settings)


@pytest.mark.asyncio
async def test_get_session_without_tenant(database):
    """Test getting session without tenant ID."""
    async with database.get_session() as session:
        assert isinstance(session, AsyncSession)


@pytest.mark.asyncio
async def test_get_session_with_tenant(database):
    """Test getting session with tenant ID."""
    tenant_id = uuid4()
    async with database.get_session(tenant_id=tenant_id) as session:
        assert isinstance(session, AsyncSession)
        # Verify tenant_id was set (would be checked in real DB)


@pytest.mark.asyncio
async def test_get_session_commit_on_success(database):
    """Test session commits on successful exit."""
    mock_session = AsyncMock(spec=AsyncSession)
    mock_session.commit = AsyncMock()
    mock_session.close = AsyncMock()

    with patch.object(database.async_session_maker, "__call__", return_value=mock_session):
        async with database.get_session() as session:
            pass

    mock_session.commit.assert_called_once()
    mock_session.close.assert_called_once()


@pytest.mark.asyncio
async def test_get_session_rollback_on_exception(database):
    """Test session rolls back on exception."""
    mock_session = AsyncMock(spec=AsyncSession)
    mock_session.rollback = AsyncMock()
    mock_session.close = AsyncMock()

    with patch.object(database.async_session_maker, "__call__", return_value=mock_session):
        try:
            async with database.get_session() as session:
                raise ValueError("Test error")
        except ValueError:
            pass

    mock_session.rollback.assert_called_once()
    mock_session.close.assert_called_once()


@pytest.mark.asyncio
async def test_close(database):
    """Test closing database connections."""
    mock_engine = AsyncMock()
    database.engine = mock_engine

    await database.close()

    mock_engine.dispose.assert_called_once()


@pytest.mark.asyncio
async def test_health_check_success(database):
    """Test health check when database is healthy."""
    mock_session = AsyncMock(spec=AsyncSession)
    mock_result = MagicMock()
    mock_result.scalar.return_value = 1
    mock_session.execute = AsyncMock(return_value=mock_result)

    with patch.object(database, "get_session") as mock_get_session:
        mock_get_session.return_value.__aenter__.return_value = mock_session
        result = await database.health_check()

    assert result is True


@pytest.mark.asyncio
async def test_health_check_failure(database):
    """Test health check when database connection fails."""
    with patch.object(database, "get_session") as mock_get_session:
        mock_get_session.return_value.__aenter__.side_effect = Exception("Connection failed")
        result = await database.health_check()

    assert result is False


def test_init_db():
    """Test database initialization."""
    settings = DatabaseSettings(database_url="postgresql+asyncpg://user:pass@localhost:5432/testdb")
    init_db(settings)
    assert db is not None
    assert db.settings == settings


@pytest.mark.asyncio
async def test_get_db_generator():
    """Test get_db dependency generator."""
    if db is None:
        pytest.skip("Database not initialized")

    async for session in get_db():
        assert isinstance(session, AsyncSession)
        break  # Just test first iteration


@pytest.mark.asyncio
async def test_get_db_with_tenant():
    """Test get_db dependency generator with tenant ID."""
    if db is None:
        pytest.skip("Database not initialized")

    tenant_id = uuid4()
    async for session in get_db(tenant_id=tenant_id):
        assert isinstance(session, AsyncSession)
        break  # Just test first iteration
