import json
from typing import List

from fastapi import Depends
from redis import Redis

from src.core.config import settings
from src.core.redis_client import get_redis_client
from src.schemas.pricing_plan import PricingPlan


class PricingPlanRepository:
    def __init__(self, redis_client: Redis = Depends(get_redis_client)):
        self.redis_client = redis_client

    def get_cached_plans(self, min_storage: int) -> List[PricingPlan] | None:
        cache_key = f"pricing_plans:min_storage_{min_storage}"
        cached_plans = self.redis_client.get(cache_key)
        if cached_plans:
            return [PricingPlan.parse_raw(plan) for plan in json.loads(cached_plans)]
        return None

    def cache_plans(self, min_storage: int, plans: List[PricingPlan]) -> None:
        cache_key = f"pricing_plans:min_storage_{min_storage}"
        self.redis_client.setex(
            cache_key,
            settings.REDIS_CACHE_TIMEOUT,
            json.dumps([plan.json() for plan in plans]),
        )
