"""Notification service main entry point."""

# --- импорты ---
import asyncio
import os
import signal
import uvicorn
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response

from notification_service.api import router
from notification_service.config import settings
from notification_service.consumer import start_consumer
from shared.utils.logger import setup_logger
from shared.middleware import PrometheusMiddleware
from shared.metrics import get_metrics, service_health

logger = setup_logger(
    __name__, level=settings.log_level, json_logs=os.getenv("JSON_LOGS", "false").lower() == "true"
)

consumer_task: asyncio.Task | None = None


# --- lifespan: RabbitMQ consumer ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for startup and shutdown events.

    Args:
        app: FastAPI application
    """
    global consumer_task

    logger.info("Starting Notification service...")
    service_health.labels(service="notification-service").set(1)

    consumer_task = asyncio.create_task(start_consumer())
    logger.info("RabbitMQ consumer started")

    logger.info("Notification service started successfully")

    yield

    logger.info("Shutting down Notification service...")
    service_health.labels(service="notification-service").set(0)
    if consumer_task:
        consumer_task.cancel()
        try:
            await consumer_task
        except asyncio.CancelledError:
            logger.info("Consumer task cancelled")
    logger.info("Notification service shut down")


app = FastAPI(
    title="Notification Service API",
    description="Notification service for sending emails, SMS, and webhooks",
    version="0.1.0",
    lifespan=lifespan,
)

# --- middleware, роуты ---
app.add_middleware(PrometheusMiddleware, service_name="notification-service")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router, prefix="/api/v1")


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "notification-service"}


@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint."""
    return Response(content=get_metrics(), media_type="text/plain")


def signal_handler(signum, frame):
    """Handle shutdown signals gracefully."""
    logger.info(f"Received signal {signum}, initiating graceful shutdown...")


# --- запуск ---
def main():
    """Run the notification service."""
    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)
    os.environ["SERVICE_NAME"] = "notification-service"

    uvicorn.run(
        "notification_service.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.env == "development",
        log_level=settings.log_level.lower(),
    )


if __name__ == "__main__":
    main()
