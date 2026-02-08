"""Prometheus metrics utilities."""

from prometheus_client import Counter, Histogram, Gauge, generate_latest, REGISTRY
from prometheus_client.openmetrics.exposition import CONTENT_TYPE_LATEST


# HTTP metrics
http_requests_total = Counter(
    "http_requests_total",
    "Total number of HTTP requests",
    ["method", "endpoint", "status_code", "service"],
)

http_request_duration_seconds = Histogram(
    "http_request_duration_seconds",
    "HTTP request duration in seconds",
    ["method", "endpoint", "status_code", "service"],
    buckets=(0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0),
)

# Payment metrics
payments_total = Counter(
    "payments_total",
    "Total number of payments",
    ["status", "payment_method", "currency", "service"],
)

payment_amount_total = Counter(
    "payment_amount_total",
    "Total payment amount",
    ["currency", "service"],
)

payment_processing_duration_seconds = Histogram(
    "payment_processing_duration_seconds",
    "Payment processing duration in seconds",
    ["status", "service"],
    buckets=(0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0, 60.0),
)

# Merchant metrics
merchants_total = Counter(
    "merchants_total",
    "Total number of merchants",
    ["action", "service"],
)

# Error metrics
errors_total = Counter(
    "errors_total",
    "Total number of errors",
    ["error_type", "service"],
)

# Active connections
active_connections = Gauge(
    "active_connections",
    "Number of active connections",
    ["service"],
)

# Database metrics
database_queries_total = Counter(
    "database_queries_total",
    "Total number of database queries",
    ["operation", "table", "service"],
)

database_query_duration_seconds = Histogram(
    "database_query_duration_seconds",
    "Database query duration in seconds",
    ["operation", "table", "service"],
    buckets=(0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0),
)

# Redis metrics
redis_operations_total = Counter(
    "redis_operations_total",
    "Total number of Redis operations",
    ["operation", "service"],
)

redis_operation_duration_seconds = Histogram(
    "redis_operation_duration_seconds",
    "Redis operation duration in seconds",
    ["operation", "service"],
    buckets=(0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5),
)

# Rate limiting metrics
rate_limit_hits_total = Counter(
    "rate_limit_hits_total",
    "Total number of rate limit hits",
    ["merchant_id", "service"],
)

# 3DS metrics
three_ds_attempts_total = Counter(
    "three_ds_attempts_total",
    "Total number of 3DS attempts",
    ["status", "service"],
)

# Service health
service_health = Gauge(
    "service_health",
    "Service health status (1=healthy, 0=unhealthy)",
    ["service"],
)


def get_metrics():
    """Get Prometheus metrics in text format."""
    return generate_latest(REGISTRY)
