"""Provider OpenAI GPT-4 Vision."""

import base64
import logging
import time
from typing import Optional

from openai import AsyncOpenAI

from .base import BaseLLMVision, AnalysisResult

logger = logging.getLogger(__name__)


class OpenAIVision(BaseLLMVision):
    """Implementação do provider OpenAI GPT-4 Vision."""

    def __init__(self, api_key: str, model: str = "gpt-4o"):
        super().__init__(api_key, model)
        self.client = AsyncOpenAI(api_key=api_key)

    @property
    def provider_name(self) -> str:
        return "openai"

    async def analyze_frame(
        self,
        image_data: bytes,
        prompt: Optional[str] = None,
    ) -> AnalysisResult:
        """Analisa um frame usando GPT-4 Vision."""
        start_time = time.time()

        try:
            # Converte imagem para base64
            image_base64 = base64.b64encode(image_data).decode("utf-8")

            # Prepara a mensagem
            messages = [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": prompt or self.ANALYSIS_PROMPT,
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{image_base64}",
                                "detail": "low",  # Usa resolução baixa para economia
                            },
                        },
                    ],
                }
            ]

            # Faz a requisição
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=500,
                temperature=0.3,
            )

            # Extrai a resposta
            response_text = response.choices[0].message.content or ""
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
            logger.error(f"Erro na análise OpenAI: {e}")
            raise

    async def health_check(self) -> bool:
        """Verifica se a API OpenAI está acessível."""
        try:
            await self.client.models.list()
            return True
        except Exception as e:
            logger.error(f"Health check OpenAI falhou: {e}")
            return False
