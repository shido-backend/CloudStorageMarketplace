import logging
from typing import List

from fastapi import Depends

from src.clients.base_provider import BaseProviderClient
from src.clients.provider_client import get_provider_clients_with_list
from src.repositories.pricing_plan_repository import PricingPlanRepository
from src.schemas.pricing_plan import PricingPlan

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class PricingPlanService:
    def __init__(
        self,
        pricing_plan_repository: PricingPlanRepository,
        provider_clients: List[BaseProviderClient],
    ):
        self.providers = provider_clients
        self.pricing_plan_repository = pricing_plan_repository

    def get_filtered_and_sorted_plans(self, min_storage: int) -> List[PricingPlan]:
        cached_plans = self.pricing_plan_repository.get_cached_plans(min_storage)
        if cached_plans:
            logger.info(f"Returning cached plans for min_storage={min_storage}")
            return cached_plans
        all_plans = []
        for provider in self.providers:
            try:
                all_plans.extend(provider.get_pricing_plans())
            except Exception as e:
                logger.error(f"Failed to get pricing plans from provider: {str(e)}")
                continue
        filtered_plans = [plan for plan in all_plans if plan.storage_gb >= min_storage]
        sorted_plans = sorted(
            filtered_plans, key=lambda plan: plan.storage_gb * plan.price_per_gb
        )

        self.pricing_plan_repository.cache_plans(min_storage, sorted_plans)
        logger.info(f"Cached {len(sorted_plans)} plans for min_storage={min_storage}")
        return sorted_plans


def get_pricing_plan_service(
    pricing_plan_repository: PricingPlanRepository = Depends(),
    provider_clients: List[BaseProviderClient] = Depends(
        get_provider_clients_with_list
    ),
):
    return PricingPlanService(pricing_plan_repository, provider_clients)
