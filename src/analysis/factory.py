"""Factory para criação de provedores LLM Vision."""

import logging
from typing import Optional

from src.config import settings, LLMProvider
from .base import BaseLLMVision
from .openai_vision import OpenAIVision
from .anthropic_vision import AnthropicVision
from .gemini_vision import GeminiVision
from .lmstudio_vision import LMStudioVision

logger = logging.getLogger(__name__)


class LLMVisionFactory:
    """Factory para criar instâncias de provedores LLM Vision."""

    _providers: dict[LLMProvider, type[BaseLLMVision]] = {
        LLMProvider.OPENAI: OpenAIVision,
        LLMProvider.ANTHROPIC: AnthropicVision,
        LLMProvider.GEMINI: GeminiVision,
        LLMProvider.LMSTUDIO: LMStudioVision,
    }

    _instance: Optional[BaseLLMVision] = None

    @classmethod
    def create(
        cls,
        provider: Optional[LLMProvider] = None,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
    ) -> BaseLLMVision:
        """Cria uma instância do provedor LLM.

        Args:
            provider: Provedor a ser usado (padrão: settings.llm_provider)
            api_key: Chave da API (padrão: settings)
            model: Modelo a ser usado (padrão: settings)

        Returns:
            Instância do provedor LLM

        Raises:
            ValueError: Se o provedor não for suportado ou API key não estiver configurada
        """
        provider = provider or settings.llm_provider
        api_key = api_key or settings.get_llm_api_key()
        model = model or settings.get_llm_model()

        if not api_key:
            raise ValueError(
                f"API key não configurada para o provedor {provider.value}. "
                f"Configure a variável de ambiente correspondente."
            )

        provider_class = cls._providers.get(provider)
        if not provider_class:
            raise ValueError(f"Provedor não suportado: {provider.value}")

        logger.info(f"Criando provedor LLM: {provider.value} com modelo {model}")
        return provider_class(api_key=api_key, model=model)

    @classmethod
    def get_instance(cls) -> BaseLLMVision:
        """Retorna uma instância singleton do provedor LLM."""
        if cls._instance is None:
            cls._instance = cls.create()
        return cls._instance

    @classmethod
    def reset_instance(cls):
        """Reseta a instância singleton."""
        cls._instance = None

    @classmethod
    def get_available_providers(cls) -> list[str]:
        """Retorna lista de provedores disponíveis."""
        return [p.value for p in cls._providers.keys()]

    @classmethod
    async def check_provider_health(
        cls,
        provider: Optional[LLMProvider] = None,
    ) -> dict:
        """Verifica a saúde de um provedor.

        Returns:
            Dict com status de saúde
        """
        try:
            instance = cls.create(provider=provider)
            healthy = await instance.health_check()
            return {
                "provider": instance.provider_name,
                "model": instance.model,
                "healthy": healthy,
                "error": None,
            }
        except Exception as e:
            return {
                "provider": provider.value if provider else settings.llm_provider.value,
                "model": None,
                "healthy": False,
                "error": str(e),
            }
