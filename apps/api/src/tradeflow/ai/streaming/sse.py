"""Server-Sent Events streaming helpers."""

from __future__ import annotations

import json
from collections.abc import AsyncIterator
from typing import Any

from tradeflow.ai.types import AIStreamChunk, AIStreamEvent


def format_sse_event(event: AIStreamEvent) -> str:
    """Format a single SSE event frame."""
    payload: dict[str, Any] = {"type": event.type, "content": event.content}
    if event.error:
        payload["error"] = event.error
    if event.metadata:
        payload["metadata"] = event.metadata
    return f"data: {json.dumps(payload)}\n\n"


async def stream_chunks_to_sse(
    chunks: AsyncIterator[AIStreamChunk],
    *,
    conversation_id: str | None = None,
) -> AsyncIterator[str]:
    """Convert provider stream chunks to SSE frames."""
    metadata: dict[str, str] = {}
    if conversation_id:
        metadata["conversation_id"] = conversation_id

    async for chunk in chunks:
        if chunk.content:
            yield format_sse_event(AIStreamEvent(type="token", content=chunk.content))
        if chunk.done:
            yield format_sse_event(
                AIStreamEvent(
                    type="done",
                    metadata={**metadata, "finish_reason": chunk.finish_reason or "stop"},
                )
            )
            return

    yield format_sse_event(AIStreamEvent(type="done", metadata=metadata))
