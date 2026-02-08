"""Gateway service main entry point."""

# --- импорты ---
import os
import signal
import uvicorn
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi

from gateway.router import router
from gateway.config import settings
from gateway.middlewares import TenantMiddleware, RateLimitMiddleware
from gateway.deps import get_redis
from shared.utils.logger import setup_logger
from shared.middleware import PrometheusMiddleware
from shared.metrics import get_metrics, service_health
from fastapi.responses import Response

logger = setup_logger(
    __name__, level=settings.log_level, json_logs=os.getenv("JSON_LOGS", "false").lower() == "true"
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for startup and shutdown events.

    Args:
        app: FastAPI application
    """
    logger.info("Starting Gateway service...")
    service_health.labels(service="gateway").set(1)
    redis_client = get_redis()
    await redis_client.connect()
    logger.info("Gateway service started successfully")

    yield

    logger.info("Shutting down Gateway service...")
    service_health.labels(service="gateway").set(0)
    await redis_client.disconnect()
    logger.info("Gateway service shut down")


def custom_openapi():
    """
    Generate custom OpenAPI schema with logo and branding.

    Returns:
        OpenAPI schema dictionary
    """
    if app.openapi_schema:
        return app.openapi_schema

    openapi_schema = get_openapi(
        title="White-Label Payment Gateway API",
        version="1.0.0",
        description="""
        # White-Label Payment Gateway API

        Comprehensive payment gateway API for processing payments, managing merchants, and handling transactions.

        ## Features
        - Multi-tenant support
        - Rate limiting
        - Payment processing
        - Merchant management

        ## Authentication
        Use `X-API-Key` header for authentication.

        ## Rate Limits
        Rate limit: 1000 requests per second per merchant.
        """,
        routes=app.routes,
    )

    # Add custom logo and branding
    openapi_schema["info"]["x-logo"] = {
        "url": "https://via.placeholder.com/200x200/4F46E5/FFFFFF?text=Payment+Gateway",
        "altText": "Payment Gateway Logo",
    }
    openapi_schema["info"]["contact"] = {
        "name": "Payment Gateway Support",
        "email": "support@paymentgateway.com",
    }
    openapi_schema["info"]["license"] = {
        "name": "Proprietary",
    }

    app.openapi_schema = openapi_schema
    return app.openapi_schema


# --- app: OpenAPI, middleware, rate limit, tenant ---
app = FastAPI(
    title="White-Label Payment Gateway API",
    description="White-label payment gateway API with multi-tenant support",
    version="1.0.0",
    lifespan=lifespan,
    openapi_url="/openapi.json",
    docs_url="/docs",
    redoc_url="/redoc",
    redirect_slashes=True,
)

app.openapi = custom_openapi

# прометей, CORS, rate limit, tenant (порядок: tenant до rate limit для api_key)
app.add_middleware(PrometheusMiddleware, service_name="gateway")
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list if settings.cors_origins_list else ["*"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
    allow_headers=["X-API-Key", "Content-Type", "Authorization", "Accept"],
    expose_headers=["X-RateLimit-Limit", "X-RateLimit-Remaining", "X-RateLimit-Reset"],
)

if settings.rate_limit_enabled:
    redis_client = get_redis()
    app.add_middleware(
        RateLimitMiddleware,
        redis_client=redis_client,
        rate_limit_requests=settings.rate_limit_requests,
    )

app.add_middleware(TenantMiddleware)


# --- роуты ---
app.include_router(router)


# --- эндпоинты: root, metrics ---
@app.get("/")
async def root():
    """
    Root endpoint.

    Returns:
        API information
    """
    return {
        "message": "White-Label Payment Gateway API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health",
        "metrics": "/metrics",
    }


@app.get("/metrics")
async def metrics():
    """
    Prometheus metrics endpoint.

    Returns:
        Prometheus metrics in text format
    """
    return Response(content=get_metrics(), media_type="text/plain")


def signal_handler(signum, frame):
    """Handle shutdown signals gracefully."""
    logger.info(f"Received signal {signum}, initiating graceful shutdown...")


# --- запуск ---
def main():
    """Run the gateway service."""
    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)
    os.environ["SERVICE_NAME"] = "gateway"

    uvicorn.run(
        "gateway.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.env == "development",
        log_level=settings.log_level.lower(),
    )


if __name__ == "__main__":
    main()
