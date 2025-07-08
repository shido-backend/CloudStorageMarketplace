import json
from uuid import UUID

import redis
from fastapi import Depends

from src.core.redis_client import get_redis_client
from src.schemas.order import Order


class OrderRepository:
    def __init__(self, redis_client: redis.Redis = Depends(get_redis_client)):
        self.redis_client = redis_client

    def save_order(self, order: Order, ttl: int = 86400) -> None:
        order_dict = order.dict()
        order_dict["order_id"] = str(order_dict["order_id"])
        self.redis_client.set(f"order:{order.order_id}", json.dumps(order_dict), ex=ttl)

    def get_order(self, order_id: UUID) -> Order | None:
        order_data = self.redis_client.get(f"order:{order_id}")
        if order_data:
            return Order(**json.loads(order_data))
        return None

    def update_order(self, order: Order, ttl: int = 86400) -> None:
        self.save_order(order, ttl)
