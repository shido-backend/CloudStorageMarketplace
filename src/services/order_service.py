import asyncio
import logging
from uuid import UUID, uuid4

from fastapi import Depends

from src.clients.provider_client import ProviderClient, get_provider_clients_with_dict
from src.repositories.order_repository import OrderRepository
from src.schemas.order import Order

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class OrderService:
    def __init__(
        self,
        order_repository: OrderRepository,
        provider_clients: dict[str, ProviderClient],
    ):
        self.order_repository = order_repository
        self.provider_clients = provider_clients

    def create_order(self, provider: str, storage_gb: int) -> Order:
        if provider not in self.provider_clients:
            raise ValueError(f"Invalid provider: {provider}")
        order_id = uuid4()
        order = Order(
            order_id=order_id,
            provider=provider,
            storage_gb=storage_gb,
            status="pending",
        )
        self.order_repository.save_order(order)
        self.provider_clients[provider].confirm_payment(order_id)
        logger.info(f"Created order {order_id} for provider {provider}")
        return order

    def get_order(self, order_id: UUID) -> Order | None:
        return self.order_repository.get_order(order_id)

    async def complete_order(self, order_id: UUID) -> None:
        await asyncio.sleep(30)
        order = self.order_repository.get_order(order_id)
        if order:
            order.status = "completed"
            self.order_repository.update_order(order)
            logger.info(f"Completed order {order_id}")


def get_order_service(
    order_repository: OrderRepository = Depends(),
    provider_clients: dict[str, ProviderClient] = Depends(
        get_provider_clients_with_dict
    ),
):
    return OrderService(order_repository, provider_clients)
