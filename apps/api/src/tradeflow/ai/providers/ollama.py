"""Ollama local model provider."""

from __future__ import annotations

import json
from collections.abc import AsyncIterator
from typing import Any

import httpx

from tradeflow.ai.providers.base import AIProvider
from tradeflow.ai.types import (
    AICompletionRequest,
    AICompletionResponse,
    AIProviderName,
    AIStreamChunk,
)


class OllamaProvider(AIProvider):
    name = AIProviderName.OLLAMA

    def __init__(
        self,
        *,
        base_url: str = "http://localhost:11434",
        default_model: str = "llama3.2",
        timeout: float = 180.0,
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._default_model = default_model
        self._timeout = timeout
        self._available: bool | None = None

    def default_model(self) -> str:
        return self._default_model

    def is_available(self) -> bool:
        return True

    def _build_payload(self, request: AICompletionRequest, *, stream: bool) -> dict[str, Any]:
        messages = [{"role": m.role.value, "content": m.content} for m in request.messages]
        return {
            "model": request.model or self._default_model,
            "messages": messages,
            "stream": stream,
            "options": {
                "temperature": request.temperature if request.temperature is not None else 0.3,
                "num_predict": request.max_tokens or 4096,
            },
        }

    async def complete(self, request: AICompletionRequest) -> AICompletionResponse:
        payload = self._build_payload(request, stream=False)
        async with httpx.AsyncClient(timeout=self._timeout) as client:
            response = await client.post(f"{self._base_url}/api/chat", json=payload)
            response.raise_for_status()
            data = response.json()

        return AICompletionResponse(
            content=data["message"]["content"],
            model=data.get("model", payload["model"]),
            provider=self.name,
            finish_reason="stop" if data.get("done") else None,
            prompt_tokens=data.get("prompt_eval_count"),
            completion_tokens=data.get("eval_count"),
        )

    async def stream(self, request: AICompletionRequest) -> AsyncIterator[AIStreamChunk]:
        payload = self._build_payload(request, stream=True)
        async with (
            httpx.AsyncClient(timeout=self._timeout) as client,
            client.stream("POST", f"{self._base_url}/api/chat", json=payload) as response,
        ):
            response.raise_for_status()
            async for line in response.aiter_lines():
                if not line.strip():
                    continue
                try:
                    data = json.loads(line)
                except json.JSONDecodeError:
                    continue
                content = data.get("message", {}).get("content") or ""
                if content:
                    yield AIStreamChunk(content=content)
                if data.get("done"):
                    yield AIStreamChunk(content="", done=True, finish_reason="stop")
                    return
