"""AI platform HTTP routes."""

from __future__ import annotations

from uuid import UUID

from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends, Request
from fastapi.responses import StreamingResponse

from tradeflow.ai.service import AIOrchestrator
from tradeflow.ai.types import AICompletionResponse, AIFeatureType
from tradeflow.core.config import Settings
from tradeflow.core.container import Container
from tradeflow.core.dependencies.ai_rate_limit import enforce_ai_rate_limit
from tradeflow.core.dependencies.auth import CurrentUser, DbSession
from tradeflow.core.responses import SuccessResponse, success
from tradeflow.features.ai.schemas import (
    AIChatRequest,
    AICompletionResponseSchema,
    AIConversationResponse,
    AIConversationSummary,
    AIMessageResponse,
    AIPromptRequest,
    AIStatusResponse,
)

router = APIRouter(
    prefix="/ai",
    tags=["AI"],
    dependencies=[Depends(enforce_ai_rate_limit)],
)


def _to_completion(data: AICompletionResponse) -> AICompletionResponseSchema:
    return AICompletionResponseSchema(
        content=data.content,
        model=data.model,
        provider=data.provider.value,
        finish_reason=data.finish_reason,
        prompt_tokens=data.prompt_tokens,
        completion_tokens=data.completion_tokens,
    )


@router.get("/status", response_model=SuccessResponse[AIStatusResponse])
@inject
async def ai_status(
    request: Request,
    user: CurrentUser,
    settings: Settings = Depends(Provide[Container.config]),
    ai: AIOrchestrator = Depends(Provide[Container.ai_orchestrator]),
) -> SuccessResponse[AIStatusResponse]:
    return success(
        AIStatusResponse(
            enabled=settings.ai_enabled,
            configured=settings.ai_configured,
            default_provider=settings.ai_default_provider,
            providers=ai.list_providers(),
        ),
        request_id=request.state.request_id,
    )


@router.post("/chat", response_model=SuccessResponse[AICompletionResponseSchema])
@inject
async def ai_chat(
    request: Request,
    db: DbSession,
    user: CurrentUser,
    payload: AIChatRequest,
    ai: AIOrchestrator = Depends(Provide[Container.ai_orchestrator]),
) -> SuccessResponse[AICompletionResponseSchema]:
    result = await ai.chat(
        db,
        user_id=user.id,
        message=payload.message,
        feature=payload.feature,
        provider=payload.provider,
        model=payload.model,
        conversation_id=payload.conversation_id,
    )
    return success(_to_completion(result), request_id=request.state.request_id)


@router.post("/chat/stream")
@inject
async def ai_chat_stream(
    db: DbSession,
    user: CurrentUser,
    payload: AIChatRequest,
    ai: AIOrchestrator = Depends(Provide[Container.ai_orchestrator]),
) -> StreamingResponse:
    stream = ai.stream_prompt(
        db,
        user_id=user.id,
        template_id="chat.general",
        question=payload.message,
        provider=payload.provider,
        model=payload.model,
        conversation_id=payload.conversation_id,
    )
    return StreamingResponse(stream, media_type="text/event-stream")


@router.get("/conversations", response_model=SuccessResponse[list[AIConversationSummary]])
@inject
async def list_conversations(
    request: Request,
    db: DbSession,
    user: CurrentUser,
    feature: AIFeatureType | None = None,
    ai: AIOrchestrator = Depends(Provide[Container.ai_orchestrator]),
) -> SuccessResponse[list[AIConversationSummary]]:
    conversations = await ai.list_conversations(db, user_id=user.id, feature=feature)
    return success(
        [
            AIConversationSummary(
                id=c.id,
                feature_type=c.feature_type,
                title=c.title,
                provider=c.provider,
                model=c.model,
                created_at=c.created_at,
                updated_at=c.updated_at,
            )
            for c in conversations
        ],
        request_id=request.state.request_id,
    )


@router.get(
    "/conversations/{conversation_id}",
    response_model=SuccessResponse[AIConversationResponse],
)
@inject
async def get_conversation(
    request: Request,
    db: DbSession,
    user: CurrentUser,
    conversation_id: UUID,
    ai: AIOrchestrator = Depends(Provide[Container.ai_orchestrator]),
) -> SuccessResponse[AIConversationResponse]:
    conversation = await ai.get_conversation(db, user_id=user.id, conversation_id=conversation_id)
    if conversation is None:
        from tradeflow.core.errors import NotFoundError

        raise NotFoundError("Conversation not found")
    return success(
        AIConversationResponse(
            id=conversation.id,
            feature_type=conversation.feature_type,
            title=conversation.title,
            provider=conversation.provider,
            model=conversation.model,
            created_at=conversation.created_at,
            updated_at=conversation.updated_at,
            messages=[
                AIMessageResponse(
                    id=m.id,
                    role=m.role,
                    content=m.content,
                    token_count=m.token_count,
                    created_at=m.created_at,
                )
                for m in conversation.messages
            ],
        ),
        request_id=request.state.request_id,
    )


@router.delete("/conversations/{conversation_id}", response_model=SuccessResponse[dict[str, bool]])
@inject
async def delete_conversation(
    request: Request,
    db: DbSession,
    user: CurrentUser,
    conversation_id: UUID,
    ai: AIOrchestrator = Depends(Provide[Container.ai_orchestrator]),
) -> SuccessResponse[dict[str, bool]]:
    deleted = await ai.delete_conversation(db, user_id=user.id, conversation_id=conversation_id)
    return success({"deleted": deleted}, request_id=request.state.request_id)


async def _run_feature_prompt(
    db: DbSession,
    user: CurrentUser,
    template_id: str,
    payload: AIPromptRequest,
    ai: AIOrchestrator,
) -> AICompletionResponseSchema:
    result = await ai.run_prompt(
        db,
        user_id=user.id,
        template_id=template_id,
        question=payload.question,
        period=payload.period,
        provider=payload.provider,
        model=payload.model,
        conversation_id=payload.conversation_id,
        use_tools=payload.use_tools,
    )
    return _to_completion(result)


@router.post("/trade/explain", response_model=SuccessResponse[AICompletionResponseSchema])
@inject
async def explain_trade(
    request: Request,
    db: DbSession,
    user: CurrentUser,
    payload: AIPromptRequest,
    ai: AIOrchestrator = Depends(Provide[Container.ai_orchestrator]),
) -> SuccessResponse[AICompletionResponseSchema]:
    return success(
        await _run_feature_prompt(db, user, "trade.explain", payload, ai),
        request_id=request.state.request_id,
    )


@router.post("/trade/summarize", response_model=SuccessResponse[AICompletionResponseSchema])
@inject
async def summarize_trades(
    request: Request,
    db: DbSession,
    user: CurrentUser,
    payload: AIPromptRequest,
    ai: AIOrchestrator = Depends(Provide[Container.ai_orchestrator]),
) -> SuccessResponse[AICompletionResponseSchema]:
    return success(
        await _run_feature_prompt(db, user, "trade.summarize", payload, ai),
        request_id=request.state.request_id,
    )


@router.post("/risk/analyze", response_model=SuccessResponse[AICompletionResponseSchema])
@inject
async def analyze_risk(
    request: Request,
    db: DbSession,
    user: CurrentUser,
    payload: AIPromptRequest,
    ai: AIOrchestrator = Depends(Provide[Container.ai_orchestrator]),
) -> SuccessResponse[AICompletionResponseSchema]:
    return success(
        await _run_feature_prompt(db, user, "risk.analyze", payload, ai),
        request_id=request.state.request_id,
    )


@router.post("/risk/daily-summary", response_model=SuccessResponse[AICompletionResponseSchema])
@inject
async def risk_daily_summary(
    request: Request,
    db: DbSession,
    user: CurrentUser,
    payload: AIPromptRequest,
    ai: AIOrchestrator = Depends(Provide[Container.ai_orchestrator]),
) -> SuccessResponse[AICompletionResponseSchema]:
    return success(
        await _run_feature_prompt(db, user, "risk.daily_summary", payload, ai),
        request_id=request.state.request_id,
    )


@router.post("/journal/summarize", response_model=SuccessResponse[AICompletionResponseSchema])
@inject
async def summarize_journal(
    request: Request,
    db: DbSession,
    user: CurrentUser,
    payload: AIPromptRequest,
    ai: AIOrchestrator = Depends(Provide[Container.ai_orchestrator]),
) -> SuccessResponse[AICompletionResponseSchema]:
    return success(
        await _run_feature_prompt(db, user, "journal.summarize", payload, ai),
        request_id=request.state.request_id,
    )


@router.post("/journal/patterns", response_model=SuccessResponse[AICompletionResponseSchema])
@inject
async def journal_patterns(
    request: Request,
    db: DbSession,
    user: CurrentUser,
    payload: AIPromptRequest,
    ai: AIOrchestrator = Depends(Provide[Container.ai_orchestrator]),
) -> SuccessResponse[AICompletionResponseSchema]:
    return success(
        await _run_feature_prompt(db, user, "journal.patterns", payload, ai),
        request_id=request.state.request_id,
    )


@router.post("/analytics/report", response_model=SuccessResponse[AICompletionResponseSchema])
@inject
async def analytics_report(
    request: Request,
    db: DbSession,
    user: CurrentUser,
    payload: AIPromptRequest,
    ai: AIOrchestrator = Depends(Provide[Container.ai_orchestrator]),
) -> SuccessResponse[AICompletionResponseSchema]:
    return success(
        await _run_feature_prompt(db, user, "analytics.report", payload, ai),
        request_id=request.state.request_id,
    )


@router.post("/analytics/insights", response_model=SuccessResponse[AICompletionResponseSchema])
@inject
async def analytics_insights(
    request: Request,
    db: DbSession,
    user: CurrentUser,
    payload: AIPromptRequest,
    ai: AIOrchestrator = Depends(Provide[Container.ai_orchestrator]),
) -> SuccessResponse[AICompletionResponseSchema]:
    return success(
        await _run_feature_prompt(db, user, "analytics.insights", payload, ai),
        request_id=request.state.request_id,
    )


@router.post("/strategy/compare", response_model=SuccessResponse[AICompletionResponseSchema])
@inject
async def strategy_compare(
    request: Request,
    db: DbSession,
    user: CurrentUser,
    payload: AIPromptRequest,
    ai: AIOrchestrator = Depends(Provide[Container.ai_orchestrator]),
) -> SuccessResponse[AICompletionResponseSchema]:
    return success(
        await _run_feature_prompt(db, user, "strategy.compare", payload, ai),
        request_id=request.state.request_id,
    )


@router.post("/strategy/optimize", response_model=SuccessResponse[AICompletionResponseSchema])
@inject
async def strategy_optimize(
    request: Request,
    db: DbSession,
    user: CurrentUser,
    payload: AIPromptRequest,
    ai: AIOrchestrator = Depends(Provide[Container.ai_orchestrator]),
) -> SuccessResponse[AICompletionResponseSchema]:
    return success(
        await _run_feature_prompt(db, user, "strategy.optimize", payload, ai),
        request_id=request.state.request_id,
    )
