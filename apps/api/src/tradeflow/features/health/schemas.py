from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, Field


class HealthStatus(StrEnum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"


class ComponentHealth(BaseModel):
    status: HealthStatus
    latency_ms: float | None = None
    message: str | None = None


class LivenessResponse(BaseModel):
    status: str = Field(default="alive")
    service: str
    version: str
    timestamp: datetime


class ReadinessResponse(BaseModel):
    status: HealthStatus
    service: str
    version: str
    timestamp: datetime
    checks: dict[str, ComponentHealth]


class HealthSummaryResponse(BaseModel):
    status: HealthStatus
    service: str
    version: str
    environment: str
    timestamp: datetime
