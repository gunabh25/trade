"""Context builders — gather platform data for AI prompts."""

from __future__ import annotations

import json
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from tradeflow.features.analytics.schemas import AnalyticsFilterParams
from tradeflow.features.analytics.service import AnalyticsService
from tradeflow.features.journal.schemas import JournalFilterParams
from tradeflow.features.journal.service import JournalService
from tradeflow.features.risk.service import RiskService


class AIContextBuilder:
    """Build structured context strings from existing services."""

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

    async def build_trade_context(self, db: AsyncSession, user_id: UUID) -> str:
        overview = await self._analytics.get_overview(db, user_id, AnalyticsFilterParams())
        payload = {
            "metrics": overview.metrics.model_dump(mode="json"),
            "top_symbols": [s.model_dump(mode="json") for s in overview.symbol_performance[:5]],
            "recent_equity": [p.model_dump(mode="json") for p in overview.equity_curve[-14:]],
        }
        return json.dumps(payload, indent=2, default=str)

    async def build_risk_context(self, db: AsyncSession, user_id: UUID) -> str:
        rules = await self._risk.list_rules(db, user_id)
        breaches = await self._risk.list_breaches(db, user_id, limit=20)
        payload = {
            "rules": [r.model_dump(mode="json") for r in rules],
            "recent_breaches": [b.model_dump(mode="json") for b in breaches],
        }
        return json.dumps(payload, indent=2, default=str)

    async def build_journal_context(
        self,
        db: AsyncSession,
        user_id: UUID,
        *,
        limit: int = 10,
    ) -> str:
        entries, _ = await self._journal.list_entries(
            db,
            user_id,
            JournalFilterParams(page=1, page_size=limit),
        )
        stats = await self._journal.get_stats(db, user_id)
        payload = {
            "stats": stats.model_dump(mode="json"),
            "entries": [e.model_dump(mode="json") for e in entries],
        }
        return json.dumps(payload, indent=2, default=str)

    async def build_analytics_context(
        self,
        db: AsyncSession,
        user_id: UUID,
        *,
        filters: AnalyticsFilterParams | None = None,
    ) -> str:
        params = filters or AnalyticsFilterParams()
        overview = await self._analytics.get_overview(db, user_id, params)
        return json.dumps(overview.model_dump(mode="json"), indent=2, default=str)

    async def build_strategy_context(self, db: AsyncSession, user_id: UUID) -> str:
        overview = await self._analytics.get_overview(db, user_id, AnalyticsFilterParams())
        strategies = await self._journal.list_strategies(db, user_id)
        payload = {
            "analytics": overview.metrics.model_dump(mode="json"),
            "session_performance": [
                s.model_dump(mode="json") for s in overview.session_performance
            ],
            "strategies": [s.model_dump(mode="json") for s in strategies],
        }
        return json.dumps(payload, indent=2, default=str)
