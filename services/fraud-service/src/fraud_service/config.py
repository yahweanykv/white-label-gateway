"""Fraud service configuration."""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Fraud service settings."""

    # Server
    host: str = "0.0.0.0"
    port: int = 8004

    # Environment
    env: str = "development"
    log_level: str = "INFO"

    # Redis
    redis_url: str = "redis://localhost:6379/1"

    # Fraud detection
    fraud_threshold: float = 0.7
    fraud_check_enabled: bool = True

    class Config:
        """Pydantic config."""

        env_file = ".env"
        case_sensitive = False


settings = Settings()

