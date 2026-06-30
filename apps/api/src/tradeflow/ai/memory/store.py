"""Conversation memory persistence."""

from __future__ import annotations

import uuid
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from tradeflow.ai.types import AIFeatureType, AIMessage, AIMessageRole
from tradeflow.core.errors import NotFoundError
from tradeflow.db.models.ai import AIConversation, AIMessageRecord


class ConversationMemoryStore:
    """Persist and retrieve AI conversation history."""

    async def create_conversation(
        self,
        db: AsyncSession,
        *,
        user_id: UUID,
        feature_type: AIFeatureType,
        title: str | None,
        provider: str,
        model: str,
    ) -> AIConversation:
        conversation = AIConversation(
            user_id=user_id,
            feature_type=feature_type.value,
            title=title,
            provider=provider,
            model=model,
        )
        db.add(conversation)
        await db.flush()
        return conversation

    async def get_conversation(
        self,
        db: AsyncSession,
        *,
        user_id: UUID,
        conversation_id: UUID,
    ) -> AIConversation | None:
        result = await db.execute(
            select(AIConversation)
            .options(selectinload(AIConversation.messages))
            .where(
                AIConversation.id == conversation_id,
                AIConversation.user_id == user_id,
            )
        )
        return result.scalar_one_or_none()

    async def list_conversations(
        self,
        db: AsyncSession,
        *,
        user_id: UUID,
        feature_type: AIFeatureType | None = None,
        limit: int = 20,
    ) -> list[AIConversation]:
        query = (
            select(AIConversation)
            .where(AIConversation.user_id == user_id)
            .order_by(AIConversation.updated_at.desc())
            .limit(limit)
        )
        if feature_type is not None:
            query = query.where(AIConversation.feature_type == feature_type.value)
        result = await db.execute(query)
        return list(result.scalars().all())

    async def append_message(
        self,
        db: AsyncSession,
        *,
        user_id: UUID,
        conversation_id: UUID,
        role: AIMessageRole,
        content: str,
        token_count: int | None = None,
        metadata: dict[str, object] | None = None,
    ) -> AIMessageRecord:
        conversation = await self.get_conversation(
            db, user_id=user_id, conversation_id=conversation_id
        )
        if conversation is None:
            raise NotFoundError("Conversation not found")
        record = AIMessageRecord(
            id=uuid.uuid4(),
            conversation_id=conversation_id,
            role=role.value,
            content=content,
            token_count=token_count,
            metadata_=metadata,
        )
        db.add(record)
        await db.flush()
        return record

    async def get_history(
        self,
        db: AsyncSession,
        *,
        user_id: UUID,
        conversation_id: UUID,
        limit: int = 20,
    ) -> list[AIMessage]:
        conversation = await self.get_conversation(
            db, user_id=user_id, conversation_id=conversation_id
        )
        if conversation is None:
            return []
        result = await db.execute(
            select(AIMessageRecord)
            .where(AIMessageRecord.conversation_id == conversation_id)
            .order_by(AIMessageRecord.created_at.asc())
            .limit(limit)
        )
        records = result.scalars().all()
        return [
            AIMessage(role=AIMessageRole(r.role), content=r.content)
            for r in records
            if r.role in {AIMessageRole.USER.value, AIMessageRole.ASSISTANT.value}
        ]

    async def delete_conversation(
        self,
        db: AsyncSession,
        *,
        user_id: UUID,
        conversation_id: UUID,
    ) -> bool:
        conversation = await self.get_conversation(
            db, user_id=user_id, conversation_id=conversation_id
        )
        if conversation is None:
            return False
        await db.delete(conversation)
        return True
