from pydantic import BaseModel, Field, validator

from src.core.config import settings


class PricingPlan(BaseModel):
    provider: str = Field(..., description="Storage provider name")
    storage_gb: int = Field(..., description="Storage capacity in GB")
    price_per_gb: float = Field(..., description="Price per GB of storage")

    @validator("provider")
    def validate_provider(cls, v):
        if v not in settings.PROVIDERS:
            raise ValueError(f"Provider must be one of {settings.PROVIDERS}")
        return v

    @validator("storage_gb")
    def validate_storage_gb(cls, v):
        if v <= 0:
            raise ValueError("Storage GB must be positive")
        return v

    @validator("price_per_gb")
    def validate_price_per_gb(cls, v):
        if v <= 0:
            raise ValueError("Price per GB must be positive")
        return v
