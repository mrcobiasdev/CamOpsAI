"""Provider Google Gemini Vision."""

import logging
import time
from typing import Optional

import google.generativeai as genai
from PIL import Image
import io

from .base import BaseLLMVision, AnalysisResult

logger = logging.getLogger(__name__)


class GeminiVision(BaseLLMVision):
    """Implementação do provider Google Gemini Vision."""

    def __init__(self, api_key: str, model: str = "gemini-pro-vision"):
        super().__init__(api_key, model)
        genai.configure(api_key=api_key)
        self.generative_model = genai.GenerativeModel(model)

    @property
    def provider_name(self) -> str:
        return "gemini"

    async def analyze_frame(
        self,
        image_data: bytes,
        prompt: Optional[str] = None,
    ) -> AnalysisResult:
        """Analisa um frame usando Gemini Vision."""
        start_time = time.time()

        try:
            # Converte bytes para PIL Image
            image = Image.open(io.BytesIO(image_data))

            # Prepara o prompt
            analysis_prompt = prompt or self.ANALYSIS_PROMPT

            # Faz a requisição (Gemini usa API síncrona)
            response = self.generative_model.generate_content(
                [analysis_prompt, image],
                generation_config=genai.types.GenerationConfig(
                    max_output_tokens=500,
                    temperature=0.3,
                ),
            )

            # Extrai a resposta
            response_text = response.text if response.text else ""
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
            logger.error(f"Erro na análise Gemini: {e}")
            raise

    async def health_check(self) -> bool:
        """Verifica se a API Gemini está acessível."""
        try:
            # Lista modelos disponíveis como teste
            models = genai.list_models()
            return any(models)
        except Exception as e:
            logger.error(f"Health check Gemini falhou: {e}")
            return False
