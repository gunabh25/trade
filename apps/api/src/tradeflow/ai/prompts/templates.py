"""Prompt template definitions for AI features."""

from __future__ import annotations

from dataclasses import dataclass

from tradeflow.ai.types import AIFeatureType


@dataclass(frozen=True, slots=True)
class PromptTemplate:
    id: str
    feature: AIFeatureType
    system: str
    user_template: str
    description: str


TRADE_ASSISTANT_SYSTEM = (
    "You are TradeFlow AI's Trade Assistant — an expert futures and "
    "prop firm trading analyst.\n"
    "Explain trades, PnL, and account performance clearly and concisely "
    "for professional traders.\n"
    "Use the provided account context. Never invent trades or numbers "
    "not in the context.\n"
    "Highlight key drivers, risk factors, and actionable insights."
)

RISK_ADVISOR_SYSTEM = (
    "You are TradeFlow AI's Risk Advisor — an institutional risk "
    "management specialist.\n"
    "Analyze exposure, position sizing, rule violations, and daily risk posture.\n"
    "Be direct about risks. Suggest concrete position sizing and risk "
    "mitigation steps.\n"
    "Never recommend exceeding defined risk limits."
)

JOURNAL_SYSTEM = (
    "You are TradeFlow AI's Journal Coach — a trading psychology and "
    "performance analyst.\n"
    "Summarize journal entries, detect emotional patterns, identify repeated "
    "mistakes, and suggest improvements.\n"
    "Be supportive but honest. Reference specific emotions, tags, and mistakes "
    "from the context."
)

ANALYTICS_SYSTEM = (
    "You are TradeFlow AI's Analytics Analyst — a quantitative trading "
    "performance specialist.\n"
    "Generate weekly/monthly reports, strategy comparisons, trade clustering "
    "insights, and performance narratives.\n"
    "Use metrics from context. Present findings with clear structure: "
    "summary, highlights, concerns, recommendations."
)

STRATEGY_SYSTEM = (
    "You are TradeFlow AI's Strategy Assistant — a systematic trading "
    "optimization expert.\n"
    "Compare strategies, identify best market sessions, analyze win/loss "
    "trends, and suggest optimizations.\n"
    "Ground all recommendations in the provided performance data."
)


PROMPT_TEMPLATES: dict[str, PromptTemplate] = {
    "trade.explain": PromptTemplate(
        id="trade.explain",
        feature=AIFeatureType.TRADE_ASSISTANT,
        system=TRADE_ASSISTANT_SYSTEM,
        user_template=(
            "Explain the following trade or PnL in plain language:\n\n"
            "{context}\n\nQuestion: {question}"
        ),
        description="Explain a specific trade or PnL movement",
    ),
    "trade.summarize": PromptTemplate(
        id="trade.summarize",
        feature=AIFeatureType.TRADE_ASSISTANT,
        system=TRADE_ASSISTANT_SYSTEM,
        user_template="Summarize recent trading activity:\n\n{context}",
        description="Summarize recent trading activity",
    ),
    "trade.qa": PromptTemplate(
        id="trade.qa",
        feature=AIFeatureType.TRADE_ASSISTANT,
        system=TRADE_ASSISTANT_SYSTEM,
        user_template="Account context:\n{context}\n\nQuestion: {question}",
        description="Answer questions about account performance",
    ),
    "risk.analyze": PromptTemplate(
        id="risk.analyze",
        feature=AIFeatureType.RISK_ADVISOR,
        system=RISK_ADVISOR_SYSTEM,
        user_template="Analyze current risk exposure:\n\n{context}",
        description="Detect overexposure and rule violations",
    ),
    "risk.position_sizing": PromptTemplate(
        id="risk.position_sizing",
        feature=AIFeatureType.RISK_ADVISOR,
        system=RISK_ADVISOR_SYSTEM,
        user_template="Suggest position sizing based on:\n\n{context}",
        description="Suggest position sizing",
    ),
    "risk.daily_summary": PromptTemplate(
        id="risk.daily_summary",
        feature=AIFeatureType.RISK_ADVISOR,
        system=RISK_ADVISOR_SYSTEM,
        user_template="Generate a daily risk summary:\n\n{context}",
        description="Daily risk summary",
    ),
    "journal.summarize": PromptTemplate(
        id="journal.summarize",
        feature=AIFeatureType.JOURNAL,
        system=JOURNAL_SYSTEM,
        user_template="Summarize these journal entries:\n\n{context}",
        description="Auto-summarize journal entries",
    ),
    "journal.patterns": PromptTemplate(
        id="journal.patterns",
        feature=AIFeatureType.JOURNAL,
        system=JOURNAL_SYSTEM,
        user_template="Detect emotional patterns and repeated mistakes:\n\n{context}",
        description="Detect emotional patterns and mistakes",
    ),
    "journal.improve": PromptTemplate(
        id="journal.improve",
        feature=AIFeatureType.JOURNAL,
        system=JOURNAL_SYSTEM,
        user_template="Suggest improvements based on:\n\n{context}",
        description="Suggest journal-based improvements",
    ),
    "analytics.report": PromptTemplate(
        id="analytics.report",
        feature=AIFeatureType.ANALYTICS,
        system=ANALYTICS_SYSTEM,
        user_template="Generate a {period} performance report:\n\n{context}",
        description="Weekly or monthly analytics report",
    ),
    "analytics.insights": PromptTemplate(
        id="analytics.insights",
        feature=AIFeatureType.ANALYTICS,
        system=ANALYTICS_SYSTEM,
        user_template="Provide performance insights and trade clustering analysis:\n\n{context}",
        description="Performance insights and clustering",
    ),
    "analytics.compare": PromptTemplate(
        id="analytics.compare",
        feature=AIFeatureType.ANALYTICS,
        system=ANALYTICS_SYSTEM,
        user_template="Compare strategies and performance:\n\n{context}",
        description="Strategy comparison report",
    ),
    "strategy.compare": PromptTemplate(
        id="strategy.compare",
        feature=AIFeatureType.STRATEGY,
        system=STRATEGY_SYSTEM,
        user_template="Compare these strategies:\n\n{context}",
        description="Compare trading strategies",
    ),
    "strategy.sessions": PromptTemplate(
        id="strategy.sessions",
        feature=AIFeatureType.STRATEGY,
        system=STRATEGY_SYSTEM,
        user_template="Identify best market sessions from:\n\n{context}",
        description="Best market session analysis",
    ),
    "strategy.optimize": PromptTemplate(
        id="strategy.optimize",
        feature=AIFeatureType.STRATEGY,
        system=STRATEGY_SYSTEM,
        user_template="Analyze win/loss trends and suggest optimizations:\n\n{context}",
        description="Win/loss trend optimization",
    ),
    "chat.general": PromptTemplate(
        id="chat.general",
        feature=AIFeatureType.TRADE_ASSISTANT,
        system=TRADE_ASSISTANT_SYSTEM,
        user_template="{question}",
        description="General AI chat",
    ),
}
