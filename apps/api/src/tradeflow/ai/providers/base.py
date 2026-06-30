"""AI provider abstraction."""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import AsyncIterator

from tradeflow.ai.types import (
    AICompletionRequest,
    AICompletionResponse,
    AIProviderName,
    AIStreamChunk,
)


class AIProvider(ABC):
    """Abstract LLM provider — OpenAI-compatible contract."""

    name: AIProviderName

    @abstractmethod
    async def complete(self, request: AICompletionRequest) -> AICompletionResponse:
        """Non-streaming completion."""

    @abstractmethod
    def stream(self, request: AICompletionRequest) -> AsyncIterator[AIStreamChunk]:
        """Token streaming completion."""

    @abstractmethod
    def default_model(self) -> str:
        """Provider default model identifier."""

    @abstractmethod
    def is_available(self) -> bool:
        """Whether the provider is configured and reachable."""
