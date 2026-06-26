from typing import Generic, TypeVar

from pydantic import BaseModel

T = TypeVar("T")


class ResponseMeta(BaseModel):
    request_id: str | None = None


class SuccessResponse(BaseModel, Generic[T]):
    data: T
    meta: ResponseMeta | None = None


def success(data: T, *, request_id: str | None = None) -> SuccessResponse[T]:
    meta = ResponseMeta(request_id=request_id) if request_id else None
    return SuccessResponse(data=data, meta=meta)
