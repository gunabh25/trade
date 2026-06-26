from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends, Request, Response, status

from tradeflow.core.container import Container
from tradeflow.core.responses import SuccessResponse, success
from tradeflow.features.health.schemas import (
    HealthStatus,
    HealthSummaryResponse,
    LivenessResponse,
    ReadinessResponse,
)
from tradeflow.features.health.service import HealthService

router = APIRouter(prefix="/health", tags=["Health"])


@router.get(
    "/live",
    response_model=SuccessResponse[LivenessResponse],
    summary="Liveness probe",
    description="Returns 200 if the process is running. Does not check dependencies.",
)
@inject
async def liveness(
    request: Request,
    health_service: HealthService = Depends(Provide[Container.health_service]),
) -> SuccessResponse[LivenessResponse]:
    request_id: str | None = getattr(request.state, "request_id", None)
    return success(health_service.get_liveness(), request_id=request_id)


@router.get(
    "/ready",
    response_model=SuccessResponse[ReadinessResponse],
    summary="Readiness probe",
    description="Returns 200 when all dependencies are reachable; 503 otherwise.",
)
@inject
async def readiness(
    request: Request,
    response: Response,
    health_service: HealthService = Depends(Provide[Container.health_service]),
) -> SuccessResponse[ReadinessResponse]:
    request_id: str | None = getattr(request.state, "request_id", None)
    result = await health_service.get_readiness()
    if result.status == HealthStatus.UNHEALTHY:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    return success(result, request_id=request_id)


@router.get(
    "/",
    response_model=SuccessResponse[HealthSummaryResponse],
    summary="Health summary",
    description="Aggregated health status for monitoring dashboards.",
)
@inject
async def health_summary(
    request: Request,
    response: Response,
    health_service: HealthService = Depends(Provide[Container.health_service]),
) -> SuccessResponse[HealthSummaryResponse]:
    request_id: str | None = getattr(request.state, "request_id", None)
    result = await health_service.get_summary()
    if result.status == HealthStatus.UNHEALTHY:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    return success(result, request_id=request_id)
