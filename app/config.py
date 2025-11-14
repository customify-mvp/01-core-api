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
    S3_PUBLIC_BUCKET: bool = True  # If False, use signed URLs
    
    # CloudFront (optional)
    CLOUDFRONT_DOMAIN: str = Field(default="")  # e.g., "d123.cloudfront.net"
    
    # Storage
    USE_LOCAL_STORAGE: bool = Field(default=True)  # True for dev, False for prod
    
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
    
    @property
    def cors_origins_list(self) -> List[str]:
        """
        Get CORS origins as list.
        
        Returns:
            List[str]: List of allowed CORS origins
        """
        if isinstance(self.CORS_ORIGINS, list):
            return self.CORS_ORIGINS
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",")]
    
    @property
    def celery_database_url(self) -> str:
        """
        Sync database URL for Celery result backend.
        
        Celery doesn't support async drivers, so convert asyncpg → psycopg2.
        Format: db+postgresql://user:pass@host:port/dbname
        
        Returns:
            str: Sync PostgreSQL URL for Celery
        """
        url = str(self.DATABASE_URL)
        # Remove +asyncpg driver
        url = url.replace("+asyncpg", "")
        # Add db+ prefix for SQLAlchemy backend
        if not url.startswith("db+"):
            url = "db+" + url
        return url
    
    @property
    def s3_base_url(self) -> str:
        """
        Get base URL for S3 objects.
        
        Returns CloudFront URL if configured, otherwise S3 direct URL.
        
        Returns:
            str: Base URL for S3 objects
        """
        if self.CLOUDFRONT_DOMAIN:
            return f"https://{self.CLOUDFRONT_DOMAIN}"
        
        return f"https://{self.S3_BUCKET_NAME}.s3.{self.AWS_REGION}.amazonaws.com"
    
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