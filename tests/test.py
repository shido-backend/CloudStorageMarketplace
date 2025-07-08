import pytest
from fastapi.testclient import TestClient

from main import app
from src.services.order_service import OrderService

client = TestClient(app)


@pytest.fixture
def mock_order_service(mocker):
    service = OrderService()
    mocker.patch.object(service, "complete_order", return_value=None)
    return service


def test_get_pricing_plans():
    response = client.get("/pricing-plans?min_storage=100")
    assert response.status_code == 200
    plans = response.json()
    assert len(plans) > 0
    assert all(plan["storage_gb"] >= 100 for plan in plans)
    assert plans == sorted(
        plans, key=lambda plan: plan["storage_gb"] * plan["price_per_gb"]
    )


def test_create_order(mock_order_service, mocker):
    mocker.patch("src.routers.orders.OrderService", return_value=mock_order_service)
    response = client.post("/orders", json={"provider": "A", "storage_gb": 100})
    assert response.status_code == 200
    order = response.json()
    mock_order_service.complete_order.assert_called_once_with(order["order_id"])
    assert order["status"] == "pending"


def test_get_order_not_found():
    response = client.get("/orders/00000000-0000-0000-0000-000000000000")
    assert response.status_code == 404
    assert response.json()["detail"] == "Order not found"


def test_get_pricing_plans_invalid_min_storage():
    response = client.get("/pricing-plans?min_storage=-1")
    assert response.status_code == 422
