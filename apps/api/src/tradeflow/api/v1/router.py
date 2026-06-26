from fastapi import APIRouter

from tradeflow.features.auth.router import router as auth_router
from tradeflow.features.broker.router import router as broker_router
from tradeflow.features.health.router import router as health_router

v1_router = APIRouter(prefix="/v1")
v1_router.include_router(health_router)
v1_router.include_router(auth_router)
v1_router.include_router(broker_router)
