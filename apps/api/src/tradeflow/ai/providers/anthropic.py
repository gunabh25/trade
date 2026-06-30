"""Anthropic Claude provider."""

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
    AIToolCall,
)


class AnthropicProvider(AIProvider):
    name = AIProviderName.ANTHROPIC

    def __init__(
        self,
        *,
        api_key: str | None,
        default_model: str = "claude-3-5-sonnet-20241022",
        timeout: float = 120.0,
    ) -> None:
        self._api_key = api_key
        self._default_model = default_model
        self._timeout = timeout

    def default_model(self) -> str:
        return self._default_model

    def is_available(self) -> bool:
        return bool(self._api_key)

    def _split_messages(self, messages: list[AIMessage]) -> tuple[str | None, list[dict[str, Any]]]:
        system = None
        converted: list[dict[str, Any]] = []
        for msg in messages:
            if msg.role == AIMessageRole.SYSTEM:
                system = msg.content
            else:
                converted.append({"role": msg.role.value, "content": msg.content})
        return system, converted

    def _headers(self) -> dict[str, str]:
        return {
            "x-api-key": self._api_key or "",
            "anthropic-version": "2023-06-01",
            "Content-Type": "application/json",
        }

    async def complete(self, request: AICompletionRequest) -> AICompletionResponse:
        if not self._api_key:
            raise RuntimeError("Anthropic API key is not configured")

        system, messages = self._split_messages(request.messages)
        payload: dict[str, Any] = {
            "model": request.model or self._default_model,
            "messages": messages,
            "max_tokens": request.max_tokens or 4096,
            "temperature": request.temperature if request.temperature is not None else 0.3,
        }
        if system:
            payload["system"] = system
        if request.tools:
            payload["tools"] = [
                {
                    "name": t.name,
                    "description": t.description,
                    "input_schema": t.parameters,
                }
                for t in request.tools
            ]

        async with httpx.AsyncClient(timeout=self._timeout) as client:
            response = await client.post(
                "https://api.anthropic.com/v1/messages",
                headers=self._headers(),
                json=payload,
            )
            response.raise_for_status()
            data = response.json()

        text_parts: list[str] = []
        tool_calls: list[AIToolCall] = []
        for block in data.get("content") or []:
            if block.get("type") == "text":
                text_parts.append(block.get("text") or "")
            elif block.get("type") == "tool_use":
                tool_calls.append(
                    AIToolCall(
                        id=block["id"],
                        name=block["name"],
                        arguments=block.get("input") or {},
                    )
                )

        usage = data.get("usage") or {}
        return AICompletionResponse(
            content="".join(text_parts),
            model=data.get("model", payload["model"]),
            provider=self.name,
            finish_reason=data.get("stop_reason"),
            tool_calls=tool_calls,
            prompt_tokens=usage.get("input_tokens"),
            completion_tokens=usage.get("output_tokens"),
        )

    async def stream(self, request: AICompletionRequest) -> AsyncIterator[AIStreamChunk]:
        if not self._api_key:
            raise RuntimeError("Anthropic API key is not configured")

        system, messages = self._split_messages(request.messages)
        payload: dict[str, Any] = {
            "model": request.model or self._default_model,
            "messages": messages,
            "max_tokens": request.max_tokens or 4096,
            "temperature": request.temperature if request.temperature is not None else 0.3,
            "stream": True,
        }
        if system:
            payload["system"] = system

        async with (
            httpx.AsyncClient(timeout=self._timeout) as client,
            client.stream(
                "POST",
                "https://api.anthropic.com/v1/messages",
                headers=self._headers(),
                json=payload,
            ) as response,
        ):
            response.raise_for_status()
            async for line in response.aiter_lines():
                if not line.startswith("data: "):
                    continue
                try:
                    data = json.loads(line[6:])
                except json.JSONDecodeError:
                    continue
                event_type = data.get("type")
                if event_type == "content_block_delta":
                    delta = data.get("delta") or {}
                    if delta.get("type") == "text_delta":
                        text = delta.get("text") or ""
                        if text:
                            yield AIStreamChunk(content=text)
                elif event_type == "message_stop":
                    yield AIStreamChunk(content="", done=True, finish_reason="stop")
                    return
