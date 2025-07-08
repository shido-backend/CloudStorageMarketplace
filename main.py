from fastapi import FastAPI

from src.core.config import settings
from src.core.redis_client import get_redis_client
from src.routers import orders, pricing_plans

app = FastAPI(
    title="Cloud Storage Marketplace API",
    description="API for aggregating cloud storage pricing plans and managing orders from multiple providers.",
    version="0.1.0",
    docs_url=settings.DOCS_URL,
    redoc_url=settings.REDOC_URL,
)


@app.on_event("startup")
async def startup_event():
    try:
        redis_client = get_redis_client()
        redis_client.ping()
        print("Connected to Redis successfully")
    except Exception as e:
        print(f"Failed to connect to Redis: {str(e)}")
        raise


@app.on_event("shutdown")
async def disconnect_from_redis():
    try:
        redis_client = get_redis_client()
        redis_client.close()
        print("Disconnected from Redis")
    except Exception as e:
        print(f"Failed to disconnect from Redis: {str(e)}")


app.include_router(pricing_plans.router)
app.include_router(orders.router)
