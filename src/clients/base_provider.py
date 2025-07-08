import json
from pathlib import Path
from typing import List
from uuid import UUID

from redis import Redis

from src.schemas.pricing_plan import PricingPlan


class BaseProviderClient:
    def __init__(self, file_name: str, redis_client: Redis):
        self.file_path = Path(__file__).parent.parent / "clients" / file_name
        self.redis_client = redis_client
        self.cache_key = f"provider_plans:{file_name}"

    def get_pricing_plans(self) -> List[PricingPlan]:
        cached = self.redis_client.get(self.cache_key)
        if cached:
            return [PricingPlan(**plan) for plan in json.loads(cached)]

        try:
            with open(self.file_path, "r") as f:
                data = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            raise ValueError(
                f"Failed to load provider plans from {self.file_path}: {str(e)}"
            )

        plans = [PricingPlan(**plan) for plan in data]
        self.redis_client.setex(
            self.cache_key, 3600, json.dumps([plan.dict() for plan in plans])
        )
        return plans

    def confirm_payment(self, order_id: UUID) -> bool:
        return True
