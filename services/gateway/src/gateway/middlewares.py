"""FastAPI middlewares."""

from typing import Optional
from uuid import UUID

from fastapi import Request, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp


class TenantMiddleware(BaseHTTPMiddleware):
    """Middleware to extract tenant_id from X-API-Key header or subdomain."""

    def __init__(self, app: ASGIApp):
        """
        Initialize tenant middleware.

        Args:
            app: ASGI application
        """
        super().__init__(app)

    async def dispatch(self, request: Request, call_next):
        """
        Process request and extract tenant_id.

        Args:
            request: FastAPI request
            call_next: Next middleware/handler

        Returns:
            Response
        """
        # Skip processing for OPTIONS requests (CORS preflight)
        if request.method == "OPTIONS":
            return await call_next(request)

        tenant_id: Optional[UUID] = None

        # Try to extract tenant_id from X-API-Key header
        api_key = request.headers.get("X-API-Key")
        if api_key:
            # Store API key in request state for later use
            request.state.api_key = api_key
            # The actual tenant_id will be extracted when get_current_merchant is called
            # and stored in request.state.merchant_id

        # Try to extract tenant_id from subdomain
        host = request.headers.get("host", "")
        if host:
            # Extract subdomain (e.g., tenant1.example.com -> tenant1)
            parts = host.split(".")
            if len(parts) > 2:
                subdomain = parts[0]
                # Store subdomain in request state
                request.state.subdomain = subdomain
                # Try to convert subdomain to UUID if it's a valid UUID format
                try:
                    tenant_id = UUID(subdomain)
                except ValueError:
                    # If not a UUID, we'll need to lookup merchant by subdomain
                    # For now, just store the subdomain
                    pass

        # Store tenant_id in request state if found
        if tenant_id:
            request.state.tenant_id = tenant_id

        response = await call_next(request)
        return response


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Middleware for rate limiting using Redis."""

    def __init__(self, app: ASGIApp, redis_client, rate_limit_requests: int = 1000):
        """
        Initialize rate limit middleware.

        Args:
            app: ASGI application
            redis_client: Redis client instance
            rate_limit_requests: Number of requests allowed per second
        """
        super().__init__(app)
        self.redis_client = redis_client
        self.rate_limit_requests = rate_limit_requests

    async def dispatch(self, request: Request, call_next):
        """
        Process request and check rate limits.

        Args:
            request: FastAPI request
            call_next: Next middleware/handler

        Returns:
            Response with rate limit headers
        """
        # Skip rate limiting for OPTIONS (CORS preflight), health, docs, and openapi endpoints
        if request.method == "OPTIONS":
            return await call_next(request)

        skip_paths = ["/health", "/docs", "/openapi.json", "/redoc", "/"]
        if request.url.path in skip_paths:
            return await call_next(request)

        # Get merchant_id from request state (set by get_current_merchant or middleware)
        merchant_id = getattr(request.state, "merchant_id", None)
        api_key = getattr(request.state, "api_key", None)

        # Determine rate limit key
        if merchant_id:
            key = f"rate_limit:merchant:{merchant_id}"
        elif api_key:
            # Use API key hash as identifier
            import hashlib

            api_key_hash = hashlib.sha256(api_key.encode()).hexdigest()[:16]
            key = f"rate_limit:api_key:{api_key_hash}"
        else:
            # Use client IP as fallback
            client_ip = request.client.host if request.client else "unknown"
            key = f"rate_limit:ip:{client_ip}"

        # Check rate limit using Redis
        await self.redis_client.connect()
        current = await self.redis_client.client.get(key)

        if current is None:
            # First request in the window
            await self.redis_client.client.set(key, "1", ex=1)
            remaining = self.rate_limit_requests - 1
        else:
            current_count = int(current)
            if current_count >= self.rate_limit_requests:
                return JSONResponse(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    content={
                        "detail": "Rate limit exceeded",
                        "retry_after": 1,
                    },
                    headers={
                        "X-RateLimit-Limit": str(self.rate_limit_requests),
                        "X-RateLimit-Remaining": "0",
                        "X-RateLimit-Reset": "1",
                        "Retry-After": "1",
                    },
                )
            # Increment counter
            await self.redis_client.client.incr(key)
            remaining = self.rate_limit_requests - current_count - 1

        response = await call_next(request)

        # Add rate limit headers
        response.headers["X-RateLimit-Limit"] = str(self.rate_limit_requests)
        response.headers["X-RateLimit-Remaining"] = str(max(0, remaining))
        response.headers["X-RateLimit-Reset"] = "1"

        return response
