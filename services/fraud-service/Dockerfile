# Builder stage
FROM python:3.11-slim as builder

ARG DEBIAN_MIRROR="https://mirror.yandex.ru/debian"
ARG SECURITY_MIRROR="https://mirror.yandex.ru/debian-security"
ENV DEBIAN_FRONTEND=noninteractive

WORKDIR /app

# Install system dependencies
RUN set -eux; \
    rm -f /etc/apt/sources.list.d/*; \
    printf "deb ${DEBIAN_MIRROR} trixie main\n" \
           "deb ${DEBIAN_MIRROR} trixie-updates main\n" \
           "deb ${SECURITY_MIRROR} trixie-security main\n" \
           > /etc/apt/sources.list; \
    apt-get update; \
    apt-get install -y --no-install-recommends \
        build-essential; \
    rm -rf /var/lib/apt/lists/*

# Install Poetry
RUN pip install --no-cache-dir poetry==1.7.1 && \
    poetry config virtualenvs.create false

# Copy shared module first (needed as dependency)
COPY shared ./shared

# Install shared first
WORKDIR /app/shared
RUN poetry install --no-dev --no-interaction

# Copy fraud-service dependency files
WORKDIR /app
COPY services/fraud-service/pyproject.toml services/fraud-service/poetry.lock* ./services/fraud-service/

# Install fraud-service dependencies (shared is now available)
WORKDIR /app/services/fraud-service
# Update lock file if pyproject.toml changed
RUN poetry lock --no-update || true
RUN poetry install --no-dev --no-interaction --no-root

# Copy application code
COPY services/fraud-service/src ./src

# Install application
RUN poetry install --no-dev --no-interaction

# Runtime stage
FROM python:3.11-slim as runtime

WORKDIR /app

# Copy only installed packages from builder
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin
COPY --from=builder /app/services/fraud-service/src /app/services/fraud-service/src
COPY --from=builder /app/services/fraud-service/pyproject.toml /app/services/fraud-service/
COPY --from=builder /app/shared /app/shared

# Create non-root user
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# Set working directory and Python path
WORKDIR /app/services/fraud-service
ENV PYTHONPATH=/app/services/fraud-service/src:/app/shared/src:$PYTHONPATH

# Expose port
EXPOSE 8004

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8004/health')"

# Run the application
CMD ["python", "-m", "fraud_service.main"]
