"""Payment service main entry point."""

import os
import signal
from contextlib import asynccontextmanager
from pathlib import Path

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from fastapi.staticfiles import StaticFiles

from payment_service.api import router
from payment_service.config import settings
from shared.database import DatabaseSettings, Base, init_db
from shared.utils.logger import setup_logger
from shared.middleware import PrometheusMiddleware
from shared.metrics import get_metrics, service_health

logger = setup_logger(
    __name__, level=settings.log_level, json_logs=os.getenv("JSON_LOGS", "false").lower() == "true"
)


async def init_database():
    """Initialize database tables."""
    from shared.database import db

    if db is None:
        logger.error("Database not initialized")
        return

    # Import models to register them with Base
    from shared.models.db import Payment  # noqa: F401

    # Create tables
    async with db.engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database tables created")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for startup and shutdown events.

    Args:
        app: FastAPI application
    """
    # Startup
    logger.info("Starting Payment service...")
    service_health.labels(service="payment-service").set(1)

    # Initialize database
    db_settings = DatabaseSettings(database_url=settings.database_url)
    init_db(db_settings)

    # Create tables
    await init_database()

    logger.info("Payment service started successfully")

    yield

    # Shutdown
    logger.info("Shutting down Payment service...")
    service_health.labels(service="payment-service").set(0)


app = FastAPI(
    title="Payment Service API",
    description="Payment processing service",
    version="0.1.0",
    lifespan=lifespan,
)

# Prometheus metrics middleware
app.add_middleware(PrometheusMiddleware, service_name="payment-service")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static assets for mock flows
static_dir = Path(__file__).resolve().parent.parent.parent / "static"
if static_dir.exists():
    app.mount("/static", StaticFiles(directory=static_dir), name="static")

# Include routers
app.include_router(router, prefix="/api/v1")


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "payment-service"}


@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint."""
    return Response(content=get_metrics(), media_type="text/plain")


def signal_handler(signum, frame):
    """Handle shutdown signals gracefully."""
    logger.info(f"Received signal {signum}, initiating graceful shutdown...")


def main():
    """Run the payment service."""
    # Set up signal handlers for graceful shutdown
    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)

    # Set service name for logging
    os.environ["SERVICE_NAME"] = "payment-service"

    uvicorn.run(
        "payment_service.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.env == "development",
        log_level=settings.log_level.lower(),
    )


if __name__ == "__main__":
    main()
