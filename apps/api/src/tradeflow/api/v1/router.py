from fastapi import APIRouter

from tradeflow.features.analytics.router import router as analytics_router
from tradeflow.features.auth.router import router as auth_router
from tradeflow.features.broker.router import router as broker_router
from tradeflow.features.copy_trading.router import router as copy_router
from tradeflow.features.health.router import router as health_router
from tradeflow.features.journal.router import router as journal_router
from tradeflow.features.notifications.router import router as notifications_router
from tradeflow.features.risk.router import router as risk_router

v1_router = APIRouter(prefix="/v1")
v1_router.include_router(health_router)
v1_router.include_router(auth_router)
v1_router.include_router(broker_router)
v1_router.include_router(copy_router)
v1_router.include_router(risk_router)
v1_router.include_router(journal_router)
v1_router.include_router(analytics_router)
v1_router.include_router(notifications_router)
