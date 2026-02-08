"""Payment service configuration."""

from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Payment service settings."""

    # Server
    host: str = Field(default="0.0.0.0")
    port: int = Field(default=8002)

    # Environment
    env: str = Field(default="development", alias="ENV")
    environment: str = Field(default="local", alias="ENVIRONMENT")
    log_level: str = Field(default="INFO")
    payment_provider: str = Field(default="mock_success", alias="PAYMENT_PROVIDER")

    # Database
    database_url: str = Field(
        default="postgresql://payment_user:payment_pass@localhost:5432/payment_db"
    )

    # External services
    fraud_service_url: str = Field(default="http://localhost:8004")
    notification_service_url: str = Field(default="http://localhost:8003")
    merchant_service_url: str = Field(default="http://localhost:8001")
    rabbitmq_url: str = Field(default="amqp://guest:guest@localhost:5672/")

    class Config:
        """Pydantic config."""

        env_file = ".env"
        case_sensitive = False


settings = Settings()
