"""Mock provider for tests and offline development."""

from __future__ import annotations

from collections.abc import AsyncIterator

from tradeflow.ai.providers.base import AIProvider
from tradeflow.ai.types import (
    AICompletionRequest,
    AICompletionResponse,
    AIProviderName,
    AIStreamChunk,
)


class MockProvider(AIProvider):
    name = AIProviderName.MOCK

    def __init__(self, default_model: str = "mock-model") -> None:
        self._default_model = default_model

    def default_model(self) -> str:
        return self._default_model

    def is_available(self) -> bool:
        return True

    async def complete(self, request: AICompletionRequest) -> AICompletionResponse:
        last_user = next(
            (m.content for m in reversed(request.messages) if m.role.value == "user"),
            "",
        )
        return AICompletionResponse(
            content=f"[Mock AI] Processed your request about: {last_user[:200]}",
            model=self._default_model,
            provider=self.name,
            finish_reason="stop",
            prompt_tokens=100,
            completion_tokens=50,
        )

    async def stream(self, request: AICompletionRequest) -> AsyncIterator[AIStreamChunk]:
        response = await self.complete(request)
        words = response.content.split(" ")
        for word in words:
            yield AIStreamChunk(content=word + " ")
        yield AIStreamChunk(content="", done=True, finish_reason="stop")
