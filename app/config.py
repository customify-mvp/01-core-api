"""
Application configuration using Pydantic Settings.

Loads configuration from environment variables and .env file.
"""

import json
from typing import List, Union
from pydantic import Field, PostgresDsn, RedisDsn, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application settings.
    
    All settings are loaded from environment variables or .env file.
    """
    
    # App
    APP_NAME: str = "Customify Core API"
    VERSION: str = "1.0.0"
    DEBUG: bool = False
    ENVIRONMENT: str = Field(
        default="production",
        pattern="^(development|staging|production)$"
    )
    
    # Server
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    
    # Database
    DATABASE_URL: PostgresDsn = Field(
        ...,
        description="PostgreSQL connection string (async)"
    )
    # Example: postgresql+asyncpg://user:pass@localhost:5432/customify_dev
    
    # Redis
    REDIS_URL: RedisDsn = Field(
        default="redis://localhost:6379/0",
        description="Redis connection string"
    )
    
    # JWT
    JWT_SECRET_KEY: str = Field(..., min_length=32)
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 10080  # 7 days
    JWT_REFRESH_TOKEN_EXPIRE_MINUTES: int = 43200  # 30 days
    
    # AWS
    AWS_REGION: str = "us-east-1"
    AWS_ACCESS_KEY_ID: str = Field(default="")
    AWS_SECRET_ACCESS_KEY: str = Field(default="")
    S3_BUCKET_NAME: str = "customify-production"
    
    # OpenAI
    OPENAI_API_KEY: str = Field(default="")
    
    # Stripe
    STRIPE_SECRET_KEY: str = Field(default="")
    STRIPE_WEBHOOK_SECRET: str = Field(default="")
    
    # Shopify
    SHOPIFY_API_KEY: str = Field(default="")
    SHOPIFY_API_SECRET: str = Field(default="")
    SHOPIFY_WEBHOOK_SECRET: str = Field(default="")
    
    # CORS
    CORS_ORIGINS: Union[str, List[str]] = [
        "http://localhost:3000",
        "http://localhost:5173",
    ]
    
    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def parse_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
        """Parse CORS_ORIGINS from JSON string or list."""
        if isinstance(v, str):
            try:
                return json.loads(v)
            except json.JSONDecodeError:
                return [origin.strip() for origin in v.split(",")]
        return v
    
    # Encryption (Fernet key for token encryption)
    ENCRYPTION_KEY: str = Field(default="")
    
    # Rate Limiting
    RATE_LIMIT_PER_MINUTE: int = 100
    
    # Pydantic v2 config
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )


# Singleton instance
settings = Settings()