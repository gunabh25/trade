"""Unit tests for AI provider layer."""

from __future__ import annotations

import pytest

from tradeflow.ai.prompts.manager import PromptManager
from tradeflow.ai.providers.mock import MockProvider
from tradeflow.ai.types import AICompletionRequest, AIMessage, AIMessageRole


@pytest.mark.unit
@pytest.mark.asyncio
async def test_mock_provider_complete() -> None:
    provider = MockProvider()
    request = AICompletionRequest(
        messages=[
            AIMessage(role=AIMessageRole.USER, content="Explain my PnL"),
        ]
    )
    response = await provider.complete(request)
    assert response.content
    assert "Mock AI" in response.content
    assert response.provider.value == "mock"


@pytest.mark.unit
@pytest.mark.asyncio
async def test_mock_provider_stream() -> None:
    provider = MockProvider()
    request = AICompletionRequest(
        messages=[AIMessage(role=AIMessageRole.USER, content="Hello")],
        stream=True,
    )
    chunks = []
    async for chunk in provider.stream(request):
        chunks.append(chunk)
    assert any(c.content for c in chunks)
    assert chunks[-1].done is True


@pytest.mark.unit
def test_prompt_manager_render() -> None:
    manager = PromptManager()
    messages = manager.render_messages(
        "trade.explain",
        variables={"context": '{"pnl": 100}', "question": "Why did I lose?"},
    )
    assert messages[0].role == AIMessageRole.SYSTEM
    assert messages[-1].role == AIMessageRole.USER
    assert "Why did I lose?" in messages[-1].content


@pytest.mark.unit
def test_prompt_templates_cover_features() -> None:
    manager = PromptManager()
    from tradeflow.ai.types import AIFeatureType

    for feature in AIFeatureType:
        templates = manager.list_by_feature(feature)
        assert len(templates) >= 1
