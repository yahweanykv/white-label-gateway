"""Merchant service configuration."""

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Merchant service settings."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Server
    host: str = Field(default="0.0.0.0", description="Server host")
    port: int = Field(default=8001, ge=1, le=65535, description="Server port")

    # Environment
    env: str = Field(default="development", description="Environment")
    log_level: str = Field(default="INFO", description="Logging level")

    # Database
    database_url: str = Field(
        default=("postgresql+asyncpg://merchant_user:merchant_pass" "@localhost:5432/merchant_db"),
        description="Database connection URL",
    )

    # Payment Service URL
    payment_service_url: str = Field(
        default="http://localhost:8002",
        description="Payment service URL",
    )

    # Auto-create demo merchant
    create_demo_merchant: bool = Field(
        default=True, description="Auto-create demo merchant on startup"
    )

    # Auto-create load test merchant (sk_test_loadtest) for Locust/load testing
    create_loadtest_merchant: bool = Field(
        default=False, description="Create load test merchant with sk_test_loadtest"
    )

    @field_validator("database_url", mode="before")
    @classmethod
    def ensure_asyncpg_scheme(cls, v: str) -> str:  # type: ignore[override]
        """Force asyncpg driver even if URL comes without it."""
        if isinstance(v, str) and v.startswith("postgresql://"):
            return v.replace("postgresql://", "postgresql+asyncpg://", 1)
        return v


settings = Settings()
