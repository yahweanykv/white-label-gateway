"""Gateway service configuration."""

from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, field_validator


class Settings(BaseSettings):
    """Gateway settings."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
        env_prefix="GATEWAY_",
    )

    # Server
    host: str = Field(default="0.0.0.0", description="Server host")
    port: int = Field(default=8000, ge=1, le=65535, description="Server port")

    # Environment
    env: str = Field(default="development", description="Environment")
    log_level: str = Field(default="INFO", description="Logging level")

    # Service URLs
    merchant_service_url: str = Field(
        default="http://localhost:8001", description="Merchant service URL"
    )
    payment_service_url: str = Field(
        default="http://localhost:8002", description="Payment service URL"
    )
    notification_service_url: str = Field(
        default="http://localhost:8003", description="Notification service URL"
    )
    fraud_service_url: str = Field(
        default="http://localhost:8004", description="Fraud service URL"
    )

    # Database
    database_url: str = Field(
        default="postgresql://merchant_user:merchant_pass@localhost:5432/merchant_db",
        description="Database connection URL",
    )

    # Redis
    redis_url: str = Field(
        default="redis://localhost:6379/0", description="Redis connection URL"
    )

    # JWT
    jwt_secret_key: str = Field(
        default="your-secret-key-change-in-production", description="JWT secret key"
    )
    jwt_algorithm: str = Field(default="HS256", description="JWT algorithm")

    # CORS (stored as simple string, parsed in property to avoid env JSON parsing issues)
    cors_origins: str = Field(
        default="http://localhost:3000,http://localhost:3001,http://localhost:8080,http://localhost:5173,http://127.0.0.1:5173,http://127.0.0.1:3000,http://127.0.0.1:3001,http://127.0.0.1:8080",
        description="CORS allowed origins (JSON list or comma-separated string)",
    )

    @property
    def cors_origins_list(self) -> list[str]:
        """Return parsed CORS origins as list."""
        import json

        value = (self.cors_origins or "").strip()
        if not value:
            return []
        if value.startswith("["):
            try:
                parsed = json.loads(value)
                if isinstance(parsed, list):
                    return [str(item) for item in parsed]
            except json.JSONDecodeError:
                pass
        return [item.strip() for item in value.split(",") if item.strip()]

    # Rate Limiting
    rate_limit_enabled: bool = Field(default=True, description="Enable rate limiting")
    rate_limit_requests: int = Field(
        default=1000, description="Rate limit requests per second"
    )
    rate_limit_window: int = Field(default=1, description="Rate limit window in seconds")


settings = Settings()

