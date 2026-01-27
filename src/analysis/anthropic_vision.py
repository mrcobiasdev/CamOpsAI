"""Provider Anthropic Claude Vision."""

import base64
import logging
import time
from typing import Optional

from anthropic import AsyncAnthropic

from .base import BaseLLMVision, AnalysisResult

logger = logging.getLogger(__name__)


class AnthropicVision(BaseLLMVision):
    """Implementação do provider Anthropic Claude Vision."""

    def __init__(self, api_key: str, model: str = "claude-sonnet-4-20250514"):
        super().__init__(api_key, model)
        self.client = AsyncAnthropic(api_key=api_key)

    @property
    def provider_name(self) -> str:
        return "anthropic"

    async def analyze_frame(
        self,
        image_data: bytes,
        prompt: Optional[str] = None,
    ) -> AnalysisResult:
        """Analisa um frame usando Claude Vision."""
        start_time = time.time()

        try:
            # Converte imagem para base64
            image_base64 = base64.b64encode(image_data).decode("utf-8")

            # Prepara a mensagem
            message = await self.client.messages.create(
                model=self.model,
                max_tokens=500,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "image",
                                "source": {
                                    "type": "base64",
                                    "media_type": "image/jpeg",
                                    "data": image_base64,
                                },
                            },
                            {
                                "type": "text",
                                "text": prompt or self.ANALYSIS_PROMPT,
                            },
                        ],
                    }
                ],
            )

            # Extrai a resposta
            response_text = ""
            for block in message.content:
                if hasattr(block, "text"):
                    response_text += block.text

            description, keywords, confidence = self.parse_response(response_text)

            processing_time = int((time.time() - start_time) * 1000)

            return AnalysisResult(
                description=description,
                keywords=keywords,
                confidence=confidence,
                raw_response=response_text,
                provider=self.provider_name,
                model=self.model,
                processing_time_ms=processing_time,
            )

        except Exception as e:
            logger.error(f"Erro na análise Anthropic: {e}")
            raise

    async def health_check(self) -> bool:
        """Verifica se a API Anthropic está acessível."""
        try:
            # Anthropic não tem endpoint de health check simples,
            # então apenas verificamos se o cliente foi criado
            return self.client is not None
        except Exception as e:
            logger.error(f"Health check Anthropic falhou: {e}")
            return False
