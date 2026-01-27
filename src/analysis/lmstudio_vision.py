"""Provider LM Studio para modelos locais com visão."""

import base64
import logging
import time
from typing import Optional

from openai import AsyncOpenAI

from src.config import settings
from .base import BaseLLMVision, AnalysisResult

logger = logging.getLogger(__name__)


class LMStudioVision(BaseLLMVision):
    """Implementação do provider LM Studio para modelos locais.

    LM Studio expõe uma API compatível com OpenAI em localhost.
    Suporta modelos com visão como LLaVA, Qwen-VL, etc.
    """

    def __init__(
        self,
        api_key: str = "lmstudio",
        model: str = "local-model",
        base_url: Optional[str] = None,
    ):
        super().__init__(api_key, model)
        self.base_url = base_url or settings.lmstudio_api_url
        self.client = AsyncOpenAI(
            api_key=api_key or "lmstudio",  # LM Studio não precisa de key real
            base_url=self.base_url,
        )

    @property
    def provider_name(self) -> str:
        return "lmstudio"

    async def analyze_frame(
        self,
        image_data: bytes,
        prompt: Optional[str] = None,
    ) -> AnalysisResult:
        """Analisa um frame usando modelo local via LM Studio."""
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
            logger.error(f"Erro na análise LM Studio: {e}")
            raise

    async def health_check(self) -> bool:
        """Verifica se o LM Studio está acessível."""
        try:
            # Tenta listar modelos para verificar conexão
            await self.client.models.list()
            return True
        except Exception as e:
            logger.error(f"Health check LM Studio falhou: {e}")
            return False
