from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query

from src.schemas.pricing_plan import PricingPlan
from src.services.pricing_plan_service import (
    PricingPlanService,
    get_pricing_plan_service,
)

router = APIRouter(prefix="/pricing-plans", tags=["pricing-plans"])


@router.get("", response_model=List[PricingPlan])
async def get_pricing_plans(
    min_storage: int = Query(
        ...,
        description="Minimum storage capacity in GB (must be non-negative)",
        ge=0,
        example=100,
    ),
    service: PricingPlanService = Depends(get_pricing_plan_service),
):
    try:
        return service.get_filtered_and_sorted_plans(min_storage)
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to fetch pricing plans: {str(e)}"
        )
