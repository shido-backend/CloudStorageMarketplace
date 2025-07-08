from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException

from src.schemas.order import Order, OrderCreate
from src.services.order_service import OrderService, get_order_service

router = APIRouter(prefix="/orders", tags=["orders"])


@router.post("", response_model=Order)
async def create_order(
    order_data: OrderCreate,
    background_tasks: BackgroundTasks,
    service: OrderService = Depends(get_order_service),
):
    try:
        order = service.create_order(order_data.provider, order_data.storage_gb)
        background_tasks.add_task(service.complete_order, order.order_id)
        return order
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{order_id}", response_model=Order)
async def get_order(order_id: UUID, service: OrderService = Depends(get_order_service)):
    order = service.get_order(order_id)
    if order is None:
        raise HTTPException(status_code=404, detail="Order not found")
    return order
