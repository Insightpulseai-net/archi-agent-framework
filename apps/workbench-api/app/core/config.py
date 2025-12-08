"""
Application Configuration
=========================
Pydantic settings for environment-based configuration.
"""

from functools import lru_cache
from typing import List, Optional

from pydantic import AnyHttpUrl, PostgresDsn, RedisDsn, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    # Application
    APP_ENV: str = "production"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    SECRET_KEY: str
    ENCRYPTION_KEY: str

    # Server
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    # Database
    DATABASE_URL: PostgresDsn
    BRONZE_SCHEMA: str = "bronze"
    SILVER_SCHEMA: str = "silver"
    GOLD_SCHEMA: str = "gold"

    # Redis
    REDIS_URL: RedisDsn = "redis://localhost:6379/0"

    # MinIO / Object Storage
    MINIO_ENDPOINT: str = "localhost:9000"
    MINIO_ACCESS_KEY: str
    MINIO_SECRET_KEY: str
    MINIO_BUCKET: str = "workbench-data"
    MINIO_SECURE: bool = False

    # Jupyter
    JUPYTER_URL: str = "http://localhost:8888"
    JUPYTER_TOKEN: str

    # Temporal
    TEMPORAL_HOST: str = "localhost:7233"
    TEMPORAL_NAMESPACE: str = "default"
    TEMPORAL_TASK_QUEUE: str = "workbench-tasks"

    # Authentication
    AUTH_PROVIDER: str = "internal"  # internal, oidc, supabase
    AUTH_URL: Optional[str] = None
    JWT_SECRET: str
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRY_HOURS: int = 8

    # Multi-tenant
    MULTI_TENANT_ENABLED: bool = False
    DEFAULT_TENANT_ID: str = "default"

    # CORS
    CORS_ORIGINS: List[str] = ["http://localhost:3000"]

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def parse_cors_origins(cls, v):
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",")]
        return v

    # External Services - Odoo
    ODOO_URL: Optional[str] = None
    ODOO_DB: Optional[str] = None
    ODOO_USER: Optional[str] = None
    ODOO_API_KEY: Optional[str] = None

    # External Services - Superset
    SUPERSET_URL: Optional[str] = None
    SUPERSET_API_KEY: Optional[str] = None

    # External Services - OCR
    OCR_SERVICE_URL: Optional[str] = None
    OCR_API_KEY: Optional[str] = None

    # External Services - MCP/Agents
    MCP_URL: Optional[str] = None
    MCP_API_KEY: Optional[str] = None

    # n8n Integration
    N8N_WEBHOOK_URL: Optional[str] = None
    N8N_API_KEY: Optional[str] = None

    # Notifications
    SLACK_WEBHOOK_URL: Optional[str] = None

    @property
    def async_database_url(self) -> str:
        """Get async database URL for SQLAlchemy."""
        url = str(self.DATABASE_URL)
        return url.replace("postgresql://", "postgresql+asyncpg://")


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


settings = get_settings()
