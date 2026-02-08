"""Notification service configuration."""

from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field


class Settings(BaseSettings):
    """Notification service settings."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Server
    host: str = Field(default="0.0.0.0", description="Server host")
    port: int = Field(default=8003, ge=1, le=65535, description="Server port")

    # Environment
    env: str = Field(default="development", description="Environment")
    log_level: str = Field(default="INFO", description="Logging level")

    # Redis
    redis_url: str = Field(
        default="redis://localhost:6379/0", description="Redis connection URL"
    )

    # RabbitMQ
    rabbitmq_url: str = Field(
        default="amqp://guest:guest@localhost:5672/", description="RabbitMQ connection URL"
    )

    # SMTP
    smtp_host: str = Field(default="smtp.example.com", description="SMTP server host")
    smtp_port: int = Field(default=587, ge=1, le=65535, description="SMTP server port")
    smtp_user: str = Field(default="", description="SMTP username")
    smtp_password: str = Field(default="", description="SMTP password")
    smtp_from_email: str = Field(
        default="noreply@example.com", description="SMTP from email address"
    )
    smtp_use_tls: bool = Field(default=True, description="Use TLS for SMTP")

    # Webhook
    webhook_secret: str = Field(
        default="webhook-secret-change-in-production",
        description="Secret key for HMAC-SHA256 webhook signing",
    )

    # Retry settings
    max_retries: int = Field(default=3, ge=1, description="Maximum number of retry attempts")
    retry_base_delay: float = Field(
        default=1.0, ge=0.1, description="Base delay in seconds for exponential backoff"
    )

    # Merchant service URL (for getting webhook URLs)
    merchant_service_url: str = Field(
        default="http://localhost:8001", description="Merchant service URL"
    )


settings = Settings()

