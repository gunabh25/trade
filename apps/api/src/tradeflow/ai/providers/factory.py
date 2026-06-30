"""Provider factory and registry."""

from __future__ import annotations

from tradeflow.ai.providers.anthropic import AnthropicProvider
from tradeflow.ai.providers.base import AIProvider
from tradeflow.ai.providers.gemini import GeminiProvider
from tradeflow.ai.providers.mock import MockProvider
from tradeflow.ai.providers.ollama import OllamaProvider
from tradeflow.ai.providers.openai import OpenAIProvider
from tradeflow.ai.types import AIProviderName
from tradeflow.core.config import Settings
from tradeflow.core.errors import ValidationError


class AIProviderRegistry:
    """Resolve configured LLM providers."""

    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._providers: dict[AIProviderName, AIProvider] = {
            AIProviderName.OPENAI: OpenAIProvider(
                api_key=settings.openai_api_key,
                base_url=settings.openai_base_url,
                default_model=settings.ai_openai_model,
            ),
            AIProviderName.ANTHROPIC: AnthropicProvider(
                api_key=settings.anthropic_api_key,
                default_model=settings.ai_anthropic_model,
            ),
            AIProviderName.GEMINI: GeminiProvider(
                api_key=settings.google_ai_api_key,
                default_model=settings.ai_gemini_model,
            ),
            AIProviderName.OLLAMA: OllamaProvider(
                base_url=settings.ollama_base_url,
                default_model=settings.ollama_default_model,
            ),
            AIProviderName.MOCK: MockProvider(default_model="mock-model"),
        }

    def get(self, name: AIProviderName | str | None = None) -> AIProvider:
        provider_name = AIProviderName(name or self._settings.ai_default_provider)
        provider = self._providers.get(provider_name)
        if provider is None:
            raise ValidationError(f"Unknown AI provider: {provider_name}")
        if not provider.is_available() and provider_name != AIProviderName.MOCK:
            if self._settings.ai_fallback_to_mock:
                return self._providers[AIProviderName.MOCK]
            raise ValidationError(f"AI provider '{provider_name}' is not configured")
        return provider

    def list_available(self) -> list[AIProviderName]:
        available: list[AIProviderName] = []
        for name, provider in self._providers.items():
            if name == AIProviderName.MOCK:
                continue
            if provider.is_available():
                available.append(name)
        if not available and self._settings.ai_fallback_to_mock:
            available.append(AIProviderName.MOCK)
        return available
