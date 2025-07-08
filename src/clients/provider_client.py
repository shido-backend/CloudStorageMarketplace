from pathlib import Path

from fastapi import Depends
from redis import Redis

from src.core.config import settings
from src.core.redis_client import get_redis_client

from .base_provider import BaseProviderClient


class ProviderClient(BaseProviderClient):
    def __init__(self, provider_name: str, redis_client: Redis):
        file_name = f"{provider_name.lower()}"
        super().__init__(file_name, redis_client)


def get_provider_client(
    provider_name: str, redis_client: Redis = Depends(get_redis_client)
):
    file_path = Path(__file__).parent / f"{provider_name.lower()}"
    if not file_path.exists():
        raise FileNotFoundError(f"Provider config file not found: {file_path}")
    return ProviderClient(provider_name, redis_client)


def get_provider_clients_with_list(redis_client: Redis = Depends(get_redis_client)):
    return [get_provider_client(f"{p}.json", redis_client) for p in settings.PROVIDERS]


def get_provider_clients_with_dict(redis_client: Redis = Depends(get_redis_client)):
    return {
        p: get_provider_client(f"{p}.json", redis_client) for p in settings.PROVIDERS
    }
