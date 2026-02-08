"""Fraud service main entry point."""

import os
import signal
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response

from fraud_service.api import router
from fraud_service.config import settings
from shared.utils.logger import setup_logger
from shared.middleware import PrometheusMiddleware
from shared.metrics import get_metrics

logger = setup_logger(
    __name__, level=settings.log_level, json_logs=os.getenv("JSON_LOGS", "false").lower() == "true"
)

app = FastAPI(
    title="Fraud Service API",
    description="Fraud detection service",
    version="0.1.0",
)

# Prometheus metrics middleware
app.add_middleware(PrometheusMiddleware, service_name="fraud-service")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(router, prefix="/api/v1")


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "fraud-service"}


@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint."""
    return Response(content=get_metrics(), media_type="text/plain")


def signal_handler(signum, frame):
    """Handle shutdown signals gracefully."""
    logger.info(f"Received signal {signum}, initiating graceful shutdown...")


def main():
    """Run the fraud service."""
    # Set up signal handlers for graceful shutdown
    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)

    # Set service name for logging
    os.environ["SERVICE_NAME"] = "fraud-service"

    uvicorn.run(
        "fraud_service.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.env == "development",
        log_level=settings.log_level.lower(),
    )


if __name__ == "__main__":
    main()
