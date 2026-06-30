"""OpenAI-compatible provider."""

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
    AIToolCall,
)
from tradeflow.core.logging import get_logger

logger = get_logger(__name__)


class OpenAIProvider(AIProvider):
    name = AIProviderName.OPENAI

    def __init__(
        self,
        *,
        api_key: str | None,
        base_url: str = "https://api.openai.com/v1",
        default_model: str = "gpt-4o-mini",
        timeout: float = 120.0,
    ) -> None:
        self._api_key = api_key
        self._base_url = base_url.rstrip("/")
        self._default_model = default_model
        self._timeout = timeout

    def default_model(self) -> str:
        return self._default_model

    def is_available(self) -> bool:
        return bool(self._api_key)

    def _headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
        }

    def _build_payload(self, request: AICompletionRequest, *, stream: bool) -> dict[str, Any]:
        messages = [{"role": m.role.value, "content": m.content} for m in request.messages]
        payload: dict[str, Any] = {
            "model": request.model or self._default_model,
            "messages": messages,
            "temperature": request.temperature if request.temperature is not None else 0.3,
            "stream": stream,
        }
        if request.max_tokens is not None:
            payload["max_tokens"] = request.max_tokens
        if request.tools:
            payload["tools"] = [
                {
                    "type": "function",
                    "function": {
                        "name": t.name,
                        "description": t.description,
                        "parameters": t.parameters,
                    },
                }
                for t in request.tools
            ]
        return payload

    async def complete(self, request: AICompletionRequest) -> AICompletionResponse:
        if not self._api_key:
            raise RuntimeError("OpenAI API key is not configured")

        payload = self._build_payload(request, stream=False)
        async with httpx.AsyncClient(timeout=self._timeout) as client:
            response = await client.post(
                f"{self._base_url}/chat/completions",
                headers=self._headers(),
                json=payload,
            )
            response.raise_for_status()
            data = response.json()

        choice = data["choices"][0]
        message = choice["message"]
        tool_calls = [
            AIToolCall(
                id=tc["id"],
                name=tc["function"]["name"],
                arguments=json.loads(tc["function"].get("arguments") or "{}"),
            )
            for tc in message.get("tool_calls") or []
        ]
        usage = data.get("usage") or {}
        return AICompletionResponse(
            content=message.get("content") or "",
            model=data.get("model", payload["model"]),
            provider=self.name,
            finish_reason=choice.get("finish_reason"),
            tool_calls=tool_calls,
            prompt_tokens=usage.get("prompt_tokens"),
            completion_tokens=usage.get("completion_tokens"),
        )

    async def stream(self, request: AICompletionRequest) -> AsyncIterator[AIStreamChunk]:
        if not self._api_key:
            raise RuntimeError("OpenAI API key is not configured")

        payload = self._build_payload(request, stream=True)
        async with (
            httpx.AsyncClient(timeout=self._timeout) as client,
            client.stream(
                "POST",
                f"{self._base_url}/chat/completions",
                headers=self._headers(),
                json=payload,
            ) as response,
        ):
            response.raise_for_status()
            async for line in response.aiter_lines():
                if not line.startswith("data: "):
                    continue
                raw = line[6:].strip()
                if raw == "[DONE]":
                    yield AIStreamChunk(content="", done=True, finish_reason="stop")
                    return
                try:
                    data = json.loads(raw)
                except json.JSONDecodeError:
                    continue
                delta = data["choices"][0].get("delta") or {}
                content = delta.get("content") or ""
                if content:
                    yield AIStreamChunk(content=content)
                if data["choices"][0].get("finish_reason"):
                    yield AIStreamChunk(
                        content="",
                        done=True,
                        finish_reason=data["choices"][0]["finish_reason"],
                    )
                    return
