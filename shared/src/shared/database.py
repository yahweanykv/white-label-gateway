"""Async SQLAlchemy 2.0 database session with tenant support."""

from contextlib import asynccontextmanager
from typing import TYPE_CHECKING, AsyncGenerator, Optional
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.engine import make_url
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase, declared_attr

if TYPE_CHECKING:
    from shared.settings import DatabaseSettings
else:
    from shared import settings

    DatabaseSettings = settings.DatabaseSettings


class Base(DeclarativeBase):
    """Base class for all database models."""

    @declared_attr.directive
    def __tablename__(cls) -> str:
        """Generate table name from class name."""
        return cls.__name__.lower() + "s"


class Database:
    """Database connection manager with tenant support."""

    def __init__(self, settings: "DatabaseSettings"):
        """
        Initialize database connection.

        Args:
            settings: Database settings
        """
        self.settings = settings

        # Normalize URL to always use async driver for PostgreSQL
        url = make_url(settings.database_url)
        if url.drivername == "postgresql":
            url = url.set(drivername="postgresql+asyncpg")

        self.engine = create_async_engine(
            url,
            echo=settings.echo,
            pool_pre_ping=True,
            pool_size=settings.pool_size,
            max_overflow=settings.max_overflow,
        )
        self.async_session_maker = async_sessionmaker(
            self.engine,
            class_=AsyncSession,
            expire_on_commit=False,
            autocommit=False,
            autoflush=False,
        )

    @asynccontextmanager
    async def get_session(
        self, tenant_id: Optional[UUID] = None
    ) -> AsyncGenerator[AsyncSession, None]:
        """
        Get async database session with optional tenant isolation.

        Args:
            tenant_id: Optional tenant ID for multi-tenancy

        Yields:
            AsyncSession: Database session
        """
        async with self.async_session_maker() as session:
            # Set tenant_id for row-level security if provided
            if tenant_id:
                await session.execute(
                    text("SET app.current_tenant_id = :tenant_id"),
                    {"tenant_id": str(tenant_id)},
                )

            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise
            finally:
                await session.close()

    async def close(self) -> None:
        """Close database connections."""
        await self.engine.dispose()

    async def health_check(self) -> bool:
        """
        Check database connection health.

        Returns:
            True if connection is healthy
        """
        try:
            async with self.get_session() as session:
                await session.execute(text("SELECT 1"))
                return True
        except Exception:
            return False


# Global database instance (will be initialized in app startup)
db: Optional[Database] = None


async def get_db(tenant_id: Optional[UUID] = None) -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency for FastAPI to get database session.

    Args:
        tenant_id: Optional tenant ID from request

    Yields:
        AsyncSession: Database session
    """
    if db is None:  # pragma: no cover - initialization guard
        raise RuntimeError("Database not initialized. Call init_db() first.")

    async with db.get_session(tenant_id=tenant_id) as session:
        yield session


def init_db(settings: "DatabaseSettings") -> Database:
    """
    Initialize global database instance.

    Args:
        settings: Database settings

    Returns:
        Database instance
    """
    global db
    db = Database(settings)
    return db

