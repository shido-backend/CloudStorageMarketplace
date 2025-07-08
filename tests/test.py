import pytest
import asyncio
import json
from pathlib import Path
from unittest.mock import AsyncMock
from fastapi.testclient import TestClient
from uuid import UUID, uuid4

from main import app
from src.services.order_service import OrderService
from src.services.pricing_plan_service import PricingPlanService
from src.schemas.order import Order
from src.schemas.pricing_plan import PricingPlan

client = TestClient(app)

@pytest.fixture
def mock_order_service(mocker):
    service = OrderService(
        order_repository=mocker.MagicMock(),
        provider_clients={"A": mocker.MagicMock(), "B": mocker.MagicMock()}
    )
    mocker.patch.object(service, "complete_order", new=AsyncMock(return_value=None))
    return service

@pytest.fixture
def mock_pricing_plan_service(mocker):
    service = mocker.MagicMock()
    service.get_filtered_and_sorted_plans.return_value = [
        PricingPlan(provider="B", storage_gb=50, price_per_gb=0.03),
        PricingPlan(provider="A", storage_gb=100, price_per_gb=0.02),
        PricingPlan(provider="B", storage_gb=150, price_per_gb=0.018),
        PricingPlan(provider="A", storage_gb=200, price_per_gb=0.015),
        PricingPlan(provider="B", storage_gb=300, price_per_gb=0.012),
        PricingPlan(provider="B", storage_gb=600, price_per_gb=0.008),
        PricingPlan(provider="B", storage_gb=1200, price_per_gb=0.004),
        PricingPlan(provider="A", storage_gb=500, price_per_gb=0.01),
        PricingPlan(provider="A", storage_gb=1000, price_per_gb=0.005),
        PricingPlan(provider="A", storage_gb=2000, price_per_gb=0.0025)
    ]
    return service

@pytest.fixture
def setup_provider_configs(tmp_path, mocker):
    provider_a = tmp_path / "a.json"
    provider_b = tmp_path / "b.json"
    provider_a.write_text(json.dumps([
        {"provider": "A", "storage_gb": 100, "price_per_gb": 0.02},
        {"provider": "A", "storage_gb": 200, "price_per_gb": 0.015},
        {"provider": "A", "storage_gb": 500, "price_per_gb": 0.01},
        {"provider": "A", "storage_gb": 1000, "price_per_gb": 0.005},
        {"provider": "A", "storage_gb": 2000, "price_per_gb": 0.0025}
    ]))
    provider_b.write_text(json.dumps([
        {"provider": "B", "storage_gb": 50, "price_per_gb": 0.03},
        {"provider": "B", "storage_gb": 150, "price_per_gb": 0.018},
        {"provider": "B", "storage_gb": 300, "price_per_gb": 0.012},
        {"provider": "B", "storage_gb": 600, "price_per_gb": 0.008},
        {"provider": "B", "storage_gb": 1200, "price_per_gb": 0.004}
    ]))
    mocker.patch(
        "src.clients.base_provider.Path",
        side_effect=lambda *args, **kwargs: tmp_path / args[0] if args else tmp_path
    )
    return tmp_path

@pytest.fixture
def mock_redis_client(mocker):
    redis_client = mocker.MagicMock()
    redis_client.get.return_value = None
    redis_client.setex.return_value = None
    return redis_client

def test_get_pricing_plans_filter_and_sort(mock_pricing_plan_service, setup_provider_configs, mock_redis_client, mocker):
    mocker.patch("src.routers.pricing_plans.get_pricing_plan_service", return_value=mock_pricing_plan_service)
    mocker.patch("src.core.redis_client.get_redis_client", return_value=mock_redis_client)
    mock_provider_clients = [
        mocker.MagicMock(get_pricing_plans=lambda: [
            PricingPlan(provider="A", storage_gb=100, price_per_gb=0.02),
            PricingPlan(provider="A", storage_gb=200, price_per_gb=0.015),
            PricingPlan(provider="A", storage_gb=500, price_per_gb=0.01),
            PricingPlan(provider="A", storage_gb=1000, price_per_gb=0.005),
            PricingPlan(provider="A", storage_gb=2000, price_per_gb=0.0025)
        ]),
        mocker.MagicMock(get_pricing_plans=lambda: [
            PricingPlan(provider="B", storage_gb=50, price_per_gb=0.03),
            PricingPlan(provider="B", storage_gb=150, price_per_gb=0.018),
            PricingPlan(provider="B", storage_gb=300, price_per_gb=0.012),
            PricingPlan(provider="B", storage_gb=600, price_per_gb=0.008),
            PricingPlan(provider="B", storage_gb=1200, price_per_gb=0.004)
        ])
    ]
    mocker.patch("src.clients.provider_client.get_provider_clients_with_list", return_value=mock_provider_clients)
    response = client.get("/pricing-plans?min_storage=50")
    assert response.status_code == 200
    plans = response.json()
    assert len(plans) == 10  
    assert plans == [
        {"provider": "B", "storage_gb": 50, "price_per_gb": 0.03},
        {"provider": "A", "storage_gb": 100, "price_per_gb": 0.02},
        {"provider": "B", "storage_gb": 150, "price_per_gb": 0.018},
        {"provider": "A", "storage_gb": 200, "price_per_gb": 0.015},
        {"provider": "B", "storage_gb": 300, "price_per_gb": 0.012},
        {"provider": "B", "storage_gb": 600, "price_per_gb": 0.008},
        {"provider": "B", "storage_gb": 1200, "price_per_gb": 0.004},
        {"provider": "A", "storage_gb": 500, "price_per_gb": 0.01},
        {"provider": "A", "storage_gb": 1000, "price_per_gb": 0.005},
        {"provider": "A", "storage_gb": 2000, "price_per_gb": 0.0025}
    ]
    for i in range(len(plans) - 1):
        assert (plans[i]["storage_gb"] * plans[i]["price_per_gb"] <=
                plans[i + 1]["storage_gb"] * plans[i + 1]["price_per_gb"])

@pytest.mark.asyncio
async def test_create_order_pending_and_complete(mock_order_service, mock_redis_client, mocker):
    mocker.patch("src.routers.orders.get_order_service", return_value=mock_order_service)
    mocker.patch("src.core.redis_client.get_redis_client", return_value=mock_redis_client)
    order_id = uuid4()
    mocker.patch("src.services.order_service.uuid4", return_value=order_id)
    mocker.patch.object(mock_order_service, "create_order", return_value=Order(
        order_id=order_id, provider="A", storage_gb=100, status="pending"
    ))
    response = client.post("/orders", json={"provider": "A", "storage_gb": 100})
    assert response.status_code == 200
    order = response.json()
    assert order["status"] == "pending"
    assert order["order_id"] == str(order_id)
    
    mocker.patch.object(mock_order_service, "get_order", return_value=Order(
        order_id=order_id, provider="A", storage_gb=100, status="completed"
    ))
    await mock_order_service.complete_order(order_id)
    response = client.get(f"/orders/{order_id}")
    assert response.status_code == 200
    order = response.json()
    assert order["status"] == "completed"

def test_get_order_not_found(mock_order_service, mock_redis_client, mocker):
    mocker.patch("src.routers.orders.get_order_service", return_value=mock_order_service)
    mocker.patch("src.core.redis_client.get_redis_client", return_value=mock_redis_client)
    mocker.patch.object(mock_order_service, "get_order", return_value=None)
    response = client.get("/orders/00000000-0000-0000-0000-000000000000")
    assert response.status_code == 404
    assert response.json()["detail"] == "Order not found"

def test_create_order_invalid_provider(mock_order_service, mock_redis_client, mocker):
    mocker.patch("src.routers.orders.get_order_service", return_value=mock_order_service)
    mocker.patch("src.core.redis_client.get_redis_client", return_value=mock_redis_client)
    response = client.post("/orders", json={"provider": "INVALID", "storage_gb": 100})
    assert response.status_code == 422
    assert "Provider must be one of" in response.json()["detail"][0]["msg"]

def test_create_order_negative_storage(mock_order_service, mock_redis_client, mocker):
    mocker.patch("src.routers.orders.get_order_service", return_value=mock_order_service)
    mocker.patch("src.core.redis_client.get_redis_client", return_value=mock_redis_client)
    response = client.post("/orders", json={"provider": "A", "storage_gb": -100})
    assert response.status_code == 422
    assert "Storage GB must be positive" in response.json()["detail"][0]["msg"]

def test_get_pricing_plans_empty_result(mock_pricing_plan_service, mock_redis_client, mocker):
    mocker.patch("src.routers.pricing_plans.get_pricing_plan_service", return_value=mock_pricing_plan_service)
    mocker.patch("src.core.redis_client.get_redis_client", return_value=mock_redis_client)
    mock_pricing_plan_service.get_filtered_and_sorted_plans.return_value = []
    response = client.get("/pricing-plans?min_storage=10000")
    assert response.status_code == 200
    assert response.json() == []