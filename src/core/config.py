from typing import List

from pydantic import Field, validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    REDIS_HOST: str = Field(
        default="localhost", env="REDIS_HOST", description="Redis server host"
    )
    REDIS_PORT: int = Field(
        default=6379, env="REDIS_PORT", ge=1, description="Redis server port"
    )
    REDIS_DECODE_RESPONSES: bool = Field(
        default=True, description="Decode Redis responses as strings"
    )
    REDIS_CACHE_TIMEOUT: int = Field(
        default=3600, ge=1, description="Cache timeout for pricing plans (seconds)"
    )
    ORDER_CACHE_TIMEOUT: int = Field(
        default=86400, ge=1, description="Cache timeout for orders (seconds)"
    )
    PROVIDERS: List[str] = Field(
        default=["A", "B"], description="List of supported storage providers"
    )
    REDIS_MAX_CONNECTIONS: int = Field(
        default=10, ge=1, description="Max Redis connections"
    )
    REDIS_SSL: bool = Field(default=False, description="Use SSL for Redis connection")
    REDIS_RETRY_ATTEMPTS: int = Field(
        default=3, ge=1, description="Number of Redis connection retry attempts"
    )
    REDIS_RETRY_DELAY: float = Field(
        default=1.0, ge=0, description="Delay between Redis retries (seconds)"
    )
    DOCS_URL: str = Field(default="/docs", description="URL for API documentation")
    REDOC_URL: str = Field(default="/redoc", description="URL for ReDoc documentation")

    @validator("PROVIDERS")
    def validate_providers(cls, v):
        if not v:
            raise ValueError("PROVIDERS list cannot be empty")
        if len(v) != len(set(v)):
            raise ValueError("PROVIDERS list must contain unique values")
        return v

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
