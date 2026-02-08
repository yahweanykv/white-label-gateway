"""Prometheus metrics middleware for FastAPI."""

import time
from typing import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from shared.metrics import (
    http_request_duration_seconds,
    http_requests_total,
    errors_total,
)


class PrometheusMiddleware(BaseHTTPMiddleware):
    """Middleware to collect Prometheus metrics for HTTP requests."""

    def __init__(self, app: ASGIApp, service_name: str = "unknown"):
        """
        Initialize Prometheus middleware.

        Args:
            app: ASGI application
            service_name: Name of the service for metrics labeling
        """
        super().__init__(app)
        self.service_name = service_name

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Process request and collect metrics.

        Args:
            request: FastAPI request
            call_next: Next middleware/handler

        Returns:
            Response with metrics collected
        """
        start_time = time.time()

        # Get endpoint path (normalize to avoid high cardinality)
        endpoint = self._normalize_path(request.url.path)

        try:
            response = await call_next(request)
            status_code = response.status_code
        except Exception as e:
            status_code = 500
            # Log error
            errors_total.labels(
                error_type=type(e).__name__,
                service=self.service_name,
            ).inc()
            raise
        finally:
            # Calculate duration
            duration = time.time() - start_time

            # Record metrics
            http_requests_total.labels(
                method=request.method,
                endpoint=endpoint,
                status_code=status_code,
                service=self.service_name,
            ).inc()

            http_request_duration_seconds.labels(
                method=request.method,
                endpoint=endpoint,
                status_code=status_code,
                service=self.service_name,
            ).observe(duration)

        return response

    @staticmethod
    def _normalize_path(path: str) -> str:
        """
        Normalize path to avoid high cardinality in metrics.

        Args:
            path: Request path

        Returns:
            Normalized path
        """
        # Replace UUIDs and IDs with placeholders
        import re

        # Replace UUIDs
        path = re.sub(
            r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}",
            "{id}",
            path,
            flags=re.IGNORECASE,
        )
        # Replace numeric IDs
        path = re.sub(r"/\d+", "/{id}", path)
        return path

