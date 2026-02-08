# Builder stage
FROM python:3.11-slim-bookworm as builder

ARG DEBIAN_MIRROR="https://mirror.yandex.ru/debian"
ARG SECURITY_MIRROR="https://mirror.yandex.ru/debian-security"
ENV DEBIAN_FRONTEND=noninteractive

WORKDIR /app

# Install system dependencies (bookworm has stable libssl/libpq)
RUN echo "deb https://mirror.yandex.ru/debian bookworm main" > /etc/apt/sources.list && \
    echo "deb https://mirror.yandex.ru/debian bookworm-updates main" >> /etc/apt/sources.list && \
    echo "deb https://mirror.yandex.ru/debian-security bookworm-security main" >> /etc/apt/sources.list && \
    apt-get update && apt-get install -y --no-install-recommends \
        build-essential \
        libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Poetry
RUN pip install --no-cache-dir poetry==1.7.1 && \
    poetry config virtualenvs.create false

# Copy shared module first (needed as dependency)
COPY shared ./shared

# Install shared first
WORKDIR /app/shared
RUN poetry install --no-dev --no-interaction

# Copy merchant-service dependency files
WORKDIR /app
COPY services/merchant-service/pyproject.toml services/merchant-service/poetry.lock* ./services/merchant-service/

# Install merchant-service dependencies (shared is now available)
WORKDIR /app/services/merchant-service
# Update lock file if pyproject.toml changed
RUN poetry lock --no-update || true
RUN poetry install --no-dev --no-interaction --no-root

# Copy application code
COPY services/merchant-service/src ./src

# Install application
RUN poetry install --no-dev --no-interaction

# Runtime stage
FROM python:3.11-slim-bookworm as runtime

ENV DEBIAN_FRONTEND=noninteractive

WORKDIR /app

# Install runtime dependencies
RUN echo "deb https://mirror.yandex.ru/debian bookworm main" > /etc/apt/sources.list && \
    echo "deb https://mirror.yandex.ru/debian bookworm-updates main" >> /etc/apt/sources.list && \
    echo "deb https://mirror.yandex.ru/debian-security bookworm-security main" >> /etc/apt/sources.list && \
    apt-get update && apt-get install -y --no-install-recommends \
        libpq5 \
    && rm -rf /var/lib/apt/lists/*

# Copy only installed packages from builder
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin
COPY --from=builder /app/services/merchant-service/src /app/services/merchant-service/src
COPY --from=builder /app/services/merchant-service/pyproject.toml /app/services/merchant-service/
COPY --from=builder /app/shared /app/shared

# Create non-root user
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# Set working directory and Python path
WORKDIR /app/services/merchant-service
ENV PYTHONPATH=/app/services/merchant-service/src:/app/shared/src:$PYTHONPATH

# Expose port
EXPOSE 8001

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8001/health')"

# Run the application
CMD ["python", "-m", "merchant_service.main"]
