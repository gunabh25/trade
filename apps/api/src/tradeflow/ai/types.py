"""Shared AI service types."""

from __future__ import annotations

from collections.abc import AsyncIterator
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any, Literal


class AIProviderName(StrEnum):
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GEMINI = "gemini"
    OLLAMA = "ollama"
    MOCK = "mock"


class AIFeatureType(StrEnum):
    TRADE_ASSISTANT = "trade_assistant"
    RISK_ADVISOR = "risk_advisor"
    JOURNAL = "journal"
    ANALYTICS = "analytics"
    STRATEGY = "strategy"


class AIMessageRole(StrEnum):
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"
    TOOL = "tool"


@dataclass(slots=True)
class AIMessage:
    role: AIMessageRole
    content: str
    name: str | None = None
    tool_call_id: str | None = None


@dataclass(slots=True)
class AIToolDefinition:
    name: str
    description: str
    parameters: dict[str, Any]


@dataclass(slots=True)
class AIToolCall:
    id: str
    name: str
    arguments: dict[str, Any]


@dataclass(slots=True)
class AICompletionRequest:
    messages: list[AIMessage]
    model: str | None = None
    temperature: float | None = None
    max_tokens: int | None = None
    tools: list[AIToolDefinition] | None = None
    stream: bool = False


@dataclass(slots=True)
class AICompletionResponse:
    content: str
    model: str
    provider: AIProviderName
    finish_reason: str | None = None
    tool_calls: list[AIToolCall] = field(default_factory=list)
    prompt_tokens: int | None = None
    completion_tokens: int | None = None


@dataclass(slots=True)
class AIStreamChunk:
    content: str
    done: bool = False
    finish_reason: str | None = None
    tool_calls: list[AIToolCall] = field(default_factory=list)


StreamEventType = Literal["token", "done", "error"]


@dataclass(slots=True)
class AIStreamEvent:
    type: StreamEventType
    content: str = ""
    error: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


AsyncStreamIterator = AsyncIterator[AIStreamChunk]
