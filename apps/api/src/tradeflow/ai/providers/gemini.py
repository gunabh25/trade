"""Google Gemini provider."""

from __future__ import annotations

import json
from collections.abc import AsyncIterator
from typing import Any

import httpx

from tradeflow.ai.providers.base import AIProvider
from tradeflow.ai.types import (
    AICompletionRequest,
    AICompletionResponse,
    AIMessage,
    AIMessageRole,
    AIProviderName,
    AIStreamChunk,
)


class GeminiProvider(AIProvider):
    name = AIProviderName.GEMINI

    def __init__(
        self,
        *,
        api_key: str | None,
        default_model: str = "gemini-1.5-flash",
        timeout: float = 120.0,
    ) -> None:
        self._api_key = api_key
        self._default_model = default_model
        self._timeout = timeout

    def default_model(self) -> str:
        return self._default_model

    def is_available(self) -> bool:
        return bool(self._api_key)

    def _build_contents(self, messages: list[AIMessage]) -> tuple[str | None, list[dict[str, Any]]]:
        system = None
        contents: list[dict[str, Any]] = []
        for msg in messages:
            if msg.role == AIMessageRole.SYSTEM:
                system = msg.content
            elif msg.role == AIMessageRole.USER:
                contents.append({"role": "user", "parts": [{"text": msg.content}]})
            elif msg.role == AIMessageRole.ASSISTANT:
                contents.append({"role": "model", "parts": [{"text": msg.content}]})
        return system, contents

    async def complete(self, request: AICompletionRequest) -> AICompletionResponse:
        if not self._api_key:
            raise RuntimeError("Google AI API key is not configured")

        model = request.model or self._default_model
        system, contents = self._build_contents(request.messages)
        payload: dict[str, Any] = {
            "contents": contents,
            "generationConfig": {
                "temperature": request.temperature if request.temperature is not None else 0.3,
                "maxOutputTokens": request.max_tokens or 4096,
            },
        }
        if system:
            payload["systemInstruction"] = {"parts": [{"text": system}]}

        url = (
            f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
            f"?key={self._api_key}"
        )
        async with httpx.AsyncClient(timeout=self._timeout) as client:
            response = await client.post(url, json=payload)
            response.raise_for_status()
            data = response.json()

        parts = data["candidates"][0]["content"]["parts"]
        text = "".join(p.get("text", "") for p in parts)
        usage = data.get("usageMetadata") or {}
        return AICompletionResponse(
            content=text,
            model=model,
            provider=self.name,
            finish_reason=data["candidates"][0].get("finishReason"),
            prompt_tokens=usage.get("promptTokenCount"),
            completion_tokens=usage.get("candidatesTokenCount"),
        )

    async def stream(self, request: AICompletionRequest) -> AsyncIterator[AIStreamChunk]:
        if not self._api_key:
            raise RuntimeError("Google AI API key is not configured")

        model = request.model or self._default_model
        system, contents = self._build_contents(request.messages)
        payload: dict[str, Any] = {
            "contents": contents,
            "generationConfig": {
                "temperature": request.temperature if request.temperature is not None else 0.3,
                "maxOutputTokens": request.max_tokens or 4096,
            },
        }
        if system:
            payload["systemInstruction"] = {"parts": [{"text": system}]}

        url = (
            f"https://generativelanguage.googleapis.com/v1beta/models/{model}:streamGenerateContent"
            f"?alt=sse&key={self._api_key}"
        )
        async with (
            httpx.AsyncClient(timeout=self._timeout) as client,
            client.stream("POST", url, json=payload) as response,
        ):
            response.raise_for_status()
            async for line in response.aiter_lines():
                if not line.startswith("data: "):
                    continue
                try:
                    data = json.loads(line[6:])
                except json.JSONDecodeError:
                    continue
                parts = data.get("candidates", [{}])[0].get("content", {}).get("parts", [])
                text = "".join(p.get("text", "") for p in parts)
                if text:
                    yield AIStreamChunk(content=text)
                finish = data.get("candidates", [{}])[0].get("finishReason")
                if finish:
                    yield AIStreamChunk(content="", done=True, finish_reason=finish)
                    return
