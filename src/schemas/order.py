from uuid import UUID

from pydantic import BaseModel, Field, validator

from src.core.config import settings


class BaseOrder(BaseModel):
    provider: str = Field(..., description="Storage provider name")
    storage_gb: int = Field(..., description="Storage capacity in GB")

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


class Order(BaseOrder):
    order_id: UUID = Field(..., description="Unique order identifier")
    status: str = Field(..., description="Order status (pending or completed)")

    @validator("status")
    def validate_status(cls, v):
        if v not in ["pending", "completed"]:
            raise ValueError("Status must be 'pending' or 'completed'")
        return v

    class Config:
        json_encoders = {UUID: str}


class OrderCreate(BaseOrder):
    pass
