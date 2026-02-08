"""Pydantic BaseSettings with service-specific prefixes."""

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class BaseServiceSettings(BaseSettings):
    """Base settings class for all services."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Common settings
    env: str = Field(default="development", description="Environment (development/production)")
    log_level: str = Field(default="INFO", description="Logging level")
    debug: bool = Field(default=False, description="Debug mode")


class DatabaseSettings(BaseSettings):
    """Database connection settings."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    database_url: str = Field(..., description="Database connection URL")
    echo: bool = Field(default=False, description="Echo SQL queries")
    pool_size: int = Field(default=5, ge=1, description="Connection pool size")
    max_overflow: int = Field(default=10, ge=0, description="Max overflow connections")


class RedisSettings(BaseSettings):
    """Redis connection settings."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    redis_url: str = Field(..., description="Redis connection URL")
    key_prefix: str = Field(default="payment_gateway", description="Redis key prefix")
    max_connections: int = Field(default=10, ge=1, description="Max Redis connections")


class GatewaySettings(BaseServiceSettings):
    """Gateway service settings."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
        env_prefix="GATEWAY_",
    )

    host: str = Field(default="0.0.0.0", description="Server host")
    port: int = Field(default=8000, ge=1, le=65535, description="Server port")
    merchant_service_url: str = Field(..., description="Merchant service URL")
    payment_service_url: str = Field(..., description="Payment service URL")
    notification_service_url: str = Field(..., description="Notification service URL")
    fraud_service_url: str = Field(..., description="Fraud service URL")
    cors_origins: list[str] = Field(
        default=["http://localhost:3000"], description="CORS allowed origins"
    )


class MerchantServiceSettings(BaseServiceSettings):
    """Merchant service settings."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
        env_prefix="MERCHANT_",
    )

    host: str = Field(default="0.0.0.0", description="Server host")
    port: int = Field(default=8001, ge=1, le=65535, description="Server port")
    database_url: str = Field(..., description="Database connection URL")


class PaymentServiceSettings(BaseServiceSettings):
    """Payment service settings."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
        env_prefix="PAYMENT_",
    )

    host: str = Field(default="0.0.0.0", description="Server host")
    port: int = Field(default=8002, ge=1, le=65535, description="Server port")
    database_url: str = Field(..., description="Database connection URL")
    fraud_service_url: str = Field(..., description="Fraud service URL")
    notification_service_url: str = Field(..., description="Notification service URL")


class NotificationServiceSettings(BaseServiceSettings):
    """Notification service settings."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
        env_prefix="NOTIFICATION_",
    )

    host: str = Field(default="0.0.0.0", description="Server host")
    port: int = Field(default=8003, ge=1, le=65535, description="Server port")
    redis_url: str = Field(..., description="Redis connection URL")
    smtp_host: str = Field(..., description="SMTP server host")
    smtp_port: int = Field(default=587, ge=1, le=65535, description="SMTP server port")
    smtp_user: str = Field(default="", description="SMTP username")
    smtp_password: str = Field(default="", description="SMTP password")
    smtp_from_email: str = Field(..., description="SMTP from email address")


class FraudServiceSettings(BaseServiceSettings):
    """Fraud service settings."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
        env_prefix="FRAUD_",
    )

    host: str = Field(default="0.0.0.0", description="Server host")
    port: int = Field(default=8004, ge=1, le=65535, description="Server port")
    redis_url: str = Field(..., description="Redis connection URL")
    fraud_threshold: float = Field(
        default=0.7, ge=0.0, le=1.0, description="Fraud detection threshold"
    )
    fraud_check_enabled: bool = Field(default=True, description="Enable fraud checking")


@lru_cache()
def get_gateway_settings() -> GatewaySettings:  # pragma: no cover
    """Get cached gateway settings."""
    return GatewaySettings()  # pragma: no cover


@lru_cache()
def get_merchant_service_settings() -> MerchantServiceSettings:  # pragma: no cover
    """Get cached merchant service settings."""
    return MerchantServiceSettings()  # pragma: no cover


@lru_cache()
def get_payment_service_settings() -> PaymentServiceSettings:  # pragma: no cover
    """Get cached payment service settings."""
    return PaymentServiceSettings()  # pragma: no cover


@lru_cache()
def get_notification_service_settings() -> NotificationServiceSettings:  # pragma: no cover
    """Get cached notification service settings."""
    return NotificationServiceSettings()  # pragma: no cover


@lru_cache()
def get_fraud_service_settings() -> FraudServiceSettings:  # pragma: no cover
    """Get cached fraud service settings."""
    return FraudServiceSettings()  # pragma: no cover
