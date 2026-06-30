"""AI feature Pydantic schemas."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from tradeflow.ai.types import AIFeatureType


class AIChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=8000)
    feature: AIFeatureType = AIFeatureType.TRADE_ASSISTANT
    conversation_id: UUID | None = None
    provider: str | None = None
    model: str | None = None


class AIPromptRequest(BaseModel):
    question: str | None = Field(default=None, max_length=8000)
    period: str = Field(default="weekly", pattern="^(weekly|monthly)$")
    conversation_id: UUID | None = None
    provider: str | None = None
    model: str | None = None
    use_tools: bool = False


class AICompletionResponseSchema(BaseModel):
    content: str
    model: str
    provider: str
    finish_reason: str | None = None
    prompt_tokens: int | None = None
    completion_tokens: int | None = None


class AIMessageResponse(BaseModel):
    id: UUID
    role: str
    content: str
    token_count: int | None
    created_at: datetime


class AIConversationResponse(BaseModel):
    id: UUID
    feature_type: str
    title: str | None
    provider: str
    model: str
    created_at: datetime
    updated_at: datetime
    messages: list[AIMessageResponse] = Field(default_factory=list)


class AIConversationSummary(BaseModel):
    id: UUID
    feature_type: str
    title: str | None
    provider: str
    model: str
    created_at: datetime
    updated_at: datetime


class AIProviderInfo(BaseModel):
    name: str
    available: bool
    default_model: str


class AIStatusResponse(BaseModel):
    enabled: bool
    configured: bool
    default_provider: str
    providers: list[str]
