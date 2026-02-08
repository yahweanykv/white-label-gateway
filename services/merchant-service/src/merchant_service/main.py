"""Merchant service main entry point."""

import os
import signal
import uvicorn
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession

from merchant_service.api import router
from merchant_service.config import settings
from merchant_service.models import Merchant
from shared.database import init_db, DatabaseSettings, Base
from shared.utils.logger import setup_logger
from shared.middleware import PrometheusMiddleware
from shared.metrics import get_metrics, service_health
from sqlalchemy import select

logger = setup_logger(
    __name__, level=settings.log_level, json_logs=os.getenv("JSON_LOGS", "false").lower() == "true"
)


async def init_database():
    """Initialize database tables."""
    from shared.database import db

    if db is None:
        logger.error("Database not initialized")
        return

    # Create tables
    async with db.engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database tables created")


async def create_demo_merchant():
    """Create demo merchant if none exists."""
    if not settings.create_demo_merchant:
        return

    from shared.database import db

    if db is None:
        logger.error("Database not initialized")
        return

    try:
        async with db.get_session() as db_session:
            # Check if any merchant exists (limit 1 to avoid scalar_one_or_none error)
            result = await db_session.execute(select(Merchant).limit(1))
            existing = result.scalar_one_or_none()

            if existing:
                logger.info("Merchants already exist, skipping demo merchant creation")
                return

            # Create demo merchant
            import secrets

            api_key = f"sk_live_{secrets.token_urlsafe(32)}"
            demo_merchant = Merchant(
                name="Demo Merchant",
                domain="demo.example.com",
                logo_url="https://via.placeholder.com/150/256569/FFFFFF?text=Demo",
                primary_color="#256569",
                background_color="#E6F2F3",
                api_keys=[api_key],
                webhook_url="https://demo.example.com/webhook",
                is_active=True,
            )

            db_session.add(demo_merchant)
            await db_session.commit()
            logger.info(f"Demo merchant created with API key: {api_key}")
    except Exception as e:
        logger.error(f"Error creating demo merchant: {e}")


LOADTEST_API_KEY = "sk_test_loadtest"


async def create_loadtest_merchant():
    """Create load test merchant with sk_test_loadtest for Locust/load testing."""
    if not settings.create_loadtest_merchant:
        return

    from shared.database import db
    from sqlalchemy.exc import IntegrityError

    if db is None:
        logger.error("Database not initialized")
        return

    try:
        async with db.get_session() as db_session:
            # Check if load test merchant already exists (limit 1 for safety)
            result = await db_session.execute(
                select(Merchant).where(Merchant.api_keys.contains([LOADTEST_API_KEY])).limit(1)
            )
            existing = result.scalar_one_or_none()

            if existing:
                logger.info("Load test merchant already exists, skipping")
                return

            # Create load test merchant
            loadtest_merchant = Merchant(
                name="Load Test Merchant",
                domain="loadtest.example.com",
                logo_url="https://via.placeholder.com/150/4F46E5/FFFFFF?text=LoadTest",
                primary_color="#4F46E5",
                background_color="#EEF2FF",
                api_keys=[LOADTEST_API_KEY],
                webhook_url="https://loadtest.example.com/webhook",
                is_active=True,
            )

            db_session.add(loadtest_merchant)
            await db_session.commit()
            logger.info(f"Load test merchant created with API key: {LOADTEST_API_KEY}")
    except IntegrityError as e:
        # Duplicate domain/key from another worker — merchant already exists
        logger.info("Load test merchant already exists (race), skipping")
    except Exception as e:
        logger.error(f"Error creating load test merchant: {e}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for startup and shutdown events.

    Args:
        app: FastAPI application
    """
    # Startup
    logger.info("Starting Merchant service...")
    service_health.labels(service="merchant-service").set(1)

    # Initialize database
    db_settings = DatabaseSettings(database_url=settings.database_url)
    init_db(db_settings)

    # Create tables
    await init_database()

    # Create demo merchant
    await create_demo_merchant()

    # Create load test merchant (for Locust/load testing)
    await create_loadtest_merchant()

    logger.info("Merchant service started successfully")

    yield

    # Shutdown
    logger.info("Shutting down Merchant service...")
    service_health.labels(service="merchant-service").set(0)


app = FastAPI(
    title="Merchant Service API",
    description="Merchant management service",
    version="0.1.0",
    lifespan=lifespan,
)

# Prometheus metrics middleware
app.add_middleware(PrometheusMiddleware, service_name="merchant-service")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add exception handler for validation errors to see what's wrong
from fastapi import Request as FastAPIRequest
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: FastAPIRequest, exc: RequestValidationError):
    """Handle validation errors with detailed logging."""
    from shared.utils.logger import setup_logger
    import os

    logger = setup_logger(
        __name__, level="INFO", json_logs=os.getenv("JSON_LOGS", "false").lower() == "true"
    )
    logger.error(f"Validation error on {request.url.path}: {exc.errors()}")
    logger.error(f"Request headers: {dict(request.headers)}")
    return JSONResponse(
        status_code=422,
        content={"detail": exc.errors(), "body": exc.body},
    )


# Include routers
app.include_router(router, prefix="/api/v1")


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "merchant-service"}


@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint."""
    return Response(content=get_metrics(), media_type="text/plain")


def signal_handler(signum, frame):
    """Handle shutdown signals gracefully."""
    logger.info(f"Received signal {signum}, initiating graceful shutdown...")


def main():
    """Run the merchant service."""
    # Set up signal handlers for graceful shutdown
    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)

    # Set service name for logging
    os.environ["SERVICE_NAME"] = "merchant-service"

    uvicorn.run(
        "merchant_service.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.env == "development",
        log_level=settings.log_level.lower(),
    )


if __name__ == "__main__":
    main()
