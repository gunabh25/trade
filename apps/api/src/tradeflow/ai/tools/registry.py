"""Tool registry and execution."""

from __future__ import annotations

import json
from typing import Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from tradeflow.ai.tools.definitions import ALL_TOOLS
from tradeflow.ai.types import AIFeatureType, AIToolCall, AIToolDefinition
from tradeflow.core.logging import get_logger
from tradeflow.features.analytics.schemas import AnalyticsFilterParams
from tradeflow.features.analytics.service import AnalyticsService
from tradeflow.features.journal.service import JournalService
from tradeflow.features.risk.service import RiskService

logger = get_logger(__name__)


class AIToolRegistry:
    """Register tools and execute tool calls against platform data."""

    def __init__(
        self,
        *,
        analytics_service: AnalyticsService,
        journal_service: JournalService,
        risk_service: RiskService,
    ) -> None:
        self._analytics = analytics_service
        self._journal = journal_service
        self._risk = risk_service

    def tools_for_feature(self, feature: AIFeatureType) -> list[AIToolDefinition]:
        from tradeflow.ai.tools.definitions import (
            ANALYTICS_TOOLS,
            JOURNAL_TOOLS,
            RISK_TOOLS,
            TRADE_TOOLS,
        )

        mapping: dict[AIFeatureType, list[AIToolDefinition]] = {
            AIFeatureType.TRADE_ASSISTANT: TRADE_TOOLS,
            AIFeatureType.RISK_ADVISOR: RISK_TOOLS,
            AIFeatureType.JOURNAL: JOURNAL_TOOLS,
            AIFeatureType.ANALYTICS: ANALYTICS_TOOLS,
            AIFeatureType.STRATEGY: ANALYTICS_TOOLS + TRADE_TOOLS,
        }
        return mapping.get(feature, ALL_TOOLS)

    async def execute(
        self,
        db: AsyncSession,
        *,
        user_id: UUID,
        tool_call: AIToolCall,
    ) -> str:
        try:
            result = await self._dispatch(db, user_id=user_id, tool_call=tool_call)
            return json.dumps(result, default=str)
        except Exception as exc:
            logger.warning("ai_tool_execution_failed", tool=tool_call.name, error=str(exc))
            return json.dumps({"error": str(exc)})

    async def _dispatch(
        self,
        db: AsyncSession,
        *,
        user_id: UUID,
        tool_call: AIToolCall,
    ) -> dict[str, Any]:
        name = tool_call.name
        args = tool_call.arguments

        if name == "get_analytics_overview":
            overview = await self._analytics.get_overview(
                db,
                user_id,
                AnalyticsFilterParams(),
            )
            return overview.model_dump(mode="json")

        if name == "get_journal_stats":
            stats = await self._journal.get_stats(db, user_id)
            return stats.model_dump(mode="json")

        if name == "get_risk_rules":
            rules = await self._risk.list_rules(db, user_id)
            return {"rules": [r.model_dump(mode="json") for r in rules]}

        if name == "get_recent_trades":
            overview = await self._analytics.get_overview(db, user_id)
            return {
                "metrics": overview.metrics.model_dump(mode="json"),
                "symbol_breakdown": [
                    s.model_dump(mode="json") for s in overview.symbol_performance[:10]
                ],
            }

        if name == "get_account_summary":
            overview = await self._analytics.get_overview(db, user_id)
            return {
                "metrics": overview.metrics.model_dump(mode="json"),
                "equity_curve_tail": [
                    p.model_dump(mode="json") for p in overview.equity_curve[-10:]
                ],
            }

        if name == "get_exposure":
            rules = await self._risk.list_rules(db, user_id)
            breaches = await self._risk.list_breaches(db, user_id, limit=10)
            return {
                "rules": [r.model_dump(mode="json") for r in rules],
                "recent_breaches": [b.model_dump(mode="json") for b in breaches],
            }

        return {"message": f"Tool '{name}' returned no data", "arguments": args}
