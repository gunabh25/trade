"""AI orchestrator — coordinates providers, prompts, memory, and tools."""

from __future__ import annotations

from collections.abc import AsyncIterator
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from tradeflow.ai.memory.store import ConversationMemoryStore
from tradeflow.ai.prompts.manager import PromptManager
from tradeflow.ai.providers.factory import AIProviderRegistry
from tradeflow.ai.streaming.sse import stream_chunks_to_sse
from tradeflow.ai.tools.context import AIContextBuilder
from tradeflow.ai.tools.registry import AIToolRegistry
from tradeflow.ai.types import (
    AICompletionRequest,
    AICompletionResponse,
    AIFeatureType,
    AIMessage,
    AIMessageRole,
)
from tradeflow.core.config import Settings
from tradeflow.core.errors import NotFoundError, ValidationError
from tradeflow.core.logging import get_logger

logger = get_logger(__name__)


class AIOrchestrator:
    """Main AI service orchestrator."""

    def __init__(
        self,
        *,
        settings: Settings,
        analytics_service,
        journal_service,
        risk_service,
    ) -> None:
        self._settings = settings
        self._providers = AIProviderRegistry(settings)
        self._prompts = PromptManager()
        self._memory = ConversationMemoryStore()
        self._tools = AIToolRegistry(
            analytics_service=analytics_service,
            journal_service=journal_service,
            risk_service=risk_service,
        )
        self._context = AIContextBuilder(
            analytics_service=analytics_service,
            journal_service=journal_service,
            risk_service=risk_service,
        )

    def list_providers(self) -> list[str]:
        return [p.value for p in self._providers.list_available()]

    async def _resolve_context(
        self,
        db: AsyncSession,
        user_id: UUID,
        feature: AIFeatureType,
    ) -> str:
        if feature == AIFeatureType.RISK_ADVISOR:
            return await self._context.build_risk_context(db, user_id)
        if feature == AIFeatureType.JOURNAL:
            return await self._context.build_journal_context(db, user_id)
        if feature in {AIFeatureType.ANALYTICS}:
            return await self._context.build_analytics_context(db, user_id)
        if feature == AIFeatureType.STRATEGY:
            return await self._context.build_strategy_context(db, user_id)
        return await self._context.build_trade_context(db, user_id)

    async def _require_conversation(
        self,
        db: AsyncSession,
        *,
        user_id: UUID,
        conversation_id: UUID,
    ) -> None:
        conversation = await self._memory.get_conversation(
            db, user_id=user_id, conversation_id=conversation_id
        )
        if conversation is None:
            raise NotFoundError("Conversation not found")

    async def run_prompt(
        self,
        db: AsyncSession,
        *,
        user_id: UUID,
        template_id: str,
        question: str | None = None,
        period: str = "weekly",
        provider: str | None = None,
        model: str | None = None,
        conversation_id: UUID | None = None,
        use_tools: bool = False,
    ) -> AICompletionResponse:
        if not self._settings.ai_enabled:
            raise ValidationError("AI features are disabled")

        template = self._prompts.get(template_id)
        context = await self._resolve_context(db, user_id, template.feature)
        variables = {"context": context, "question": question or "", "period": period}

        history: list[AIMessage] = []
        if conversation_id:
            await self._require_conversation(db, user_id=user_id, conversation_id=conversation_id)
            history = await self._memory.get_history(
                db, user_id=user_id, conversation_id=conversation_id
            )

        messages = self._prompts.render_messages(
            template_id,
            variables=variables,
            history=history,
        )

        llm = self._providers.get(provider)
        request = AICompletionRequest(
            messages=messages,
            model=model,
            temperature=self._settings.ai_temperature,
            max_tokens=self._settings.ai_max_tokens,
            tools=self._tools.tools_for_feature(template.feature) if use_tools else None,
        )

        response = await llm.complete(request)

        if response.tool_calls and use_tools:
            for call in response.tool_calls:
                tool_result = await self._tools.execute(db, user_id=user_id, tool_call=call)
                messages.append(
                    AIMessage(
                        role=AIMessageRole.ASSISTANT,
                        content=response.content or f"Calling tool {call.name}",
                    )
                )
                messages.append(
                    AIMessage(role=AIMessageRole.USER, content=f"Tool result: {tool_result}")
                )
            follow_up = AICompletionRequest(
                messages=messages,
                model=model or llm.default_model(),
                temperature=self._settings.ai_temperature,
                max_tokens=self._settings.ai_max_tokens,
            )
            response = await llm.complete(follow_up)

        conv_id = conversation_id
        if conv_id is None:
            conversation = await self._memory.create_conversation(
                db,
                user_id=user_id,
                feature_type=template.feature,
                title=question[:80] if question else template.description,
                provider=response.provider.value,
                model=response.model,
            )
            conv_id = conversation.id
        await self._memory.append_message(
            db,
            user_id=user_id,
            conversation_id=conv_id,
            role=AIMessageRole.USER,
            content=variables.get("question") or template.description,
        )
        await self._memory.append_message(
            db,
            user_id=user_id,
            conversation_id=conv_id,
            role=AIMessageRole.ASSISTANT,
            content=response.content,
            token_count=response.completion_tokens,
        )

        return response

    async def stream_prompt(
        self,
        db: AsyncSession,
        *,
        user_id: UUID,
        template_id: str,
        question: str,
        provider: str | None = None,
        model: str | None = None,
        conversation_id: UUID | None = None,
    ) -> AsyncIterator[str]:
        if not self._settings.ai_enabled:
            raise ValidationError("AI features are disabled")

        template = self._prompts.get(template_id)
        context = await self._resolve_context(db, user_id, template.feature)
        history: list[AIMessage] = []
        if conversation_id:
            await self._require_conversation(db, user_id=user_id, conversation_id=conversation_id)
            history = await self._memory.get_history(
                db, user_id=user_id, conversation_id=conversation_id
            )

        messages = self._prompts.render_messages(
            template_id,
            variables={"context": context, "question": question, "period": "weekly"},
            history=history,
        )

        llm = self._providers.get(provider)
        request = AICompletionRequest(
            messages=messages,
            model=model,
            temperature=self._settings.ai_temperature,
            max_tokens=self._settings.ai_max_tokens,
            stream=True,
        )

        conv_id = conversation_id
        if conv_id is None:
            conversation = await self._memory.create_conversation(
                db,
                user_id=user_id,
                feature_type=template.feature,
                title=question[:80],
                provider=llm.name.value,
                model=model or llm.default_model(),
            )
            conv_id = conversation.id

        await self._memory.append_message(
            db,
            user_id=user_id,
            conversation_id=conv_id,
            role=AIMessageRole.USER,
            content=question,
        )

        collected: list[str] = []
        async for frame in stream_chunks_to_sse(
            llm.stream(request),
            conversation_id=str(conv_id),
        ):
            if '"type": "token"' in frame:
                import json

                data = json.loads(frame.removeprefix("data: ").strip())
                collected.append(data.get("content", ""))
            yield frame

        if collected:
            await self._memory.append_message(
                db,
                user_id=user_id,
                conversation_id=conv_id,
                role=AIMessageRole.ASSISTANT,
                content="".join(collected),
            )

    async def chat(
        self,
        db: AsyncSession,
        *,
        user_id: UUID,
        message: str,
        feature: AIFeatureType = AIFeatureType.TRADE_ASSISTANT,
        provider: str | None = None,
        model: str | None = None,
        conversation_id: UUID | None = None,
    ) -> AICompletionResponse:
        template_id = "chat.general"
        context = await self._resolve_context(db, user_id, feature)
        full_question = f"Context:\n{context}\n\nUser message: {message}"
        return await self.run_prompt(
            db,
            user_id=user_id,
            template_id=template_id,
            question=full_question,
            provider=provider,
            model=model,
            conversation_id=conversation_id,
        )

    async def list_conversations(
        self,
        db: AsyncSession,
        *,
        user_id: UUID,
        feature: AIFeatureType | None = None,
    ):
        return await self._memory.list_conversations(db, user_id=user_id, feature_type=feature)

    async def get_conversation(
        self,
        db: AsyncSession,
        *,
        user_id: UUID,
        conversation_id: UUID,
    ):
        return await self._memory.get_conversation(
            db, user_id=user_id, conversation_id=conversation_id
        )

    async def delete_conversation(
        self,
        db: AsyncSession,
        *,
        user_id: UUID,
        conversation_id: UUID,
    ) -> bool:
        return await self._memory.delete_conversation(
            db, user_id=user_id, conversation_id=conversation_id
        )
