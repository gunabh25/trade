"""AI tool definitions for function calling."""

from __future__ import annotations

from tradeflow.ai.types import AIToolDefinition

TRADE_TOOLS: list[AIToolDefinition] = [
    AIToolDefinition(
        name="get_account_summary",
        description="Fetch account balances, open PnL, and active positions summary",
        parameters={
            "type": "object",
            "properties": {},
            "required": [],
        },
    ),
    AIToolDefinition(
        name="get_recent_trades",
        description="Fetch recent closed trades for analysis",
        parameters={
            "type": "object",
            "properties": {
                "limit": {"type": "integer", "description": "Number of trades", "default": 10},
            },
            "required": [],
        },
    ),
]

RISK_TOOLS: list[AIToolDefinition] = [
    AIToolDefinition(
        name="get_risk_rules",
        description="Fetch active risk rules and current breach status",
        parameters={"type": "object", "properties": {}, "required": []},
    ),
    AIToolDefinition(
        name="get_exposure",
        description="Fetch current portfolio exposure by symbol and account",
        parameters={"type": "object", "properties": {}, "required": []},
    ),
]

JOURNAL_TOOLS: list[AIToolDefinition] = [
    AIToolDefinition(
        name="get_journal_stats",
        description="Fetch journal statistics including emotions and mistakes",
        parameters={"type": "object", "properties": {}, "required": []},
    ),
]

ANALYTICS_TOOLS: list[AIToolDefinition] = [
    AIToolDefinition(
        name="get_analytics_overview",
        description="Fetch analytics overview metrics for the user",
        parameters={
            "type": "object",
            "properties": {
                "days": {
                    "type": "integer",
                    "description": "Lookback period in days",
                    "default": 30,
                },
            },
            "required": [],
        },
    ),
]

ALL_TOOLS = TRADE_TOOLS + RISK_TOOLS + JOURNAL_TOOLS + ANALYTICS_TOOLS
