"""Prompt template manager."""

from __future__ import annotations

from tradeflow.ai.prompts.templates import PROMPT_TEMPLATES, PromptTemplate
from tradeflow.ai.types import AIFeatureType, AIMessage, AIMessageRole
from tradeflow.core.errors import NotFoundError


class PromptManager:
    """Load and render prompt templates."""

    def get(self, template_id: str) -> PromptTemplate:
        template = PROMPT_TEMPLATES.get(template_id)
        if template is None:
            raise NotFoundError(f"Prompt template '{template_id}' not found")
        return template

    def list_by_feature(self, feature: AIFeatureType) -> list[PromptTemplate]:
        return [t for t in PROMPT_TEMPLATES.values() if t.feature == feature]

    def render_messages(
        self,
        template_id: str,
        *,
        variables: dict[str, str],
        history: list[AIMessage] | None = None,
    ) -> list[AIMessage]:
        template = self.get(template_id)
        user_content = template.user_template.format(**variables)
        messages: list[AIMessage] = [
            AIMessage(role=AIMessageRole.SYSTEM, content=template.system),
        ]
        if history:
            messages.extend(history)
        messages.append(AIMessage(role=AIMessageRole.USER, content=user_content))
        return messages
