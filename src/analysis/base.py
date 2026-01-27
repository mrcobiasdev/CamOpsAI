"""Interface base para provedores de LLM Vision."""

import json
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class AnalysisResult:
    """Resultado da análise de um frame."""

    description: str
    keywords: List[str] = field(default_factory=list)
    confidence: Optional[float] = None
    raw_response: Optional[str] = None
    provider: Optional[str] = None
    model: Optional[str] = None
    processing_time_ms: Optional[int] = None

    def to_dict(self) -> dict:
        """Converte para dicionário."""
        return {
            "description": self.description,
            "keywords": self.keywords,
            "confidence": self.confidence,
            "provider": self.provider,
            "model": self.model,
            "processing_time_ms": self.processing_time_ms,
        }


class BaseLLMVision(ABC):
    """Interface base para provedores de LLM com capacidade de visão."""

    ANALYSIS_PROMPT = """Analise esta imagem de câmera de segurança e descreva o que está acontecendo.

Responda em formato JSON com a seguinte estrutura:
{
    "description": "Descrição detalhada do que está acontecendo na cena",
    "keywords": ["lista", "de", "palavras", "chave", "relevantes"],
    "confidence": 0.95
}

Foque em:
- Pessoas presentes e suas ações
- Veículos e movimentos
- Objetos suspeitos ou incomuns
- Atividades relevantes para segurança
- Condições ambientais (iluminação, clima se visível)

Seja objetivo e preciso. As palavras-chave devem ser termos simples que descrevam os elementos principais da cena.
Responda APENAS com o JSON, sem texto adicional."""

    def __init__(self, api_key: str, model: str):
        self.api_key = api_key
        self.model = model

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Nome do provedor."""
        pass

    @abstractmethod
    async def analyze_frame(
        self,
        image_data: bytes,
        prompt: Optional[str] = None,
    ) -> AnalysisResult:
        """Analisa um frame de imagem.

        Args:
            image_data: Bytes da imagem (JPEG)
            prompt: Prompt customizado (opcional)

        Returns:
            AnalysisResult com a descrição e palavras-chave
        """
        pass

    def parse_response(self, response_text: str) -> tuple[str, List[str], Optional[float]]:
        """Extrai descrição, keywords e confiança da resposta."""
        try:
            # Tenta extrair JSON da resposta
            json_str = response_text.strip()

            # Remove possíveis marcadores de código
            if json_str.startswith("```"):
                lines = json_str.split("\n")
                json_str = "\n".join(lines[1:-1])

            data = json.loads(json_str)

            description = data.get("description", response_text)
            keywords = data.get("keywords", [])
            confidence = data.get("confidence")

            return description, keywords, confidence

        except json.JSONDecodeError:
            # Fallback: usa a resposta como descrição
            return response_text, self._extract_keywords(response_text), None

    def _extract_keywords(self, text: str) -> List[str]:
        """Extrai palavras-chave básicas do texto."""
        # Lista de palavras comuns a ignorar
        stop_words = {
            "a", "o", "e", "de", "da", "do", "em", "um", "uma", "para",
            "com", "que", "na", "no", "se", "por", "mais", "como", "mas",
            "foi", "são", "está", "este", "esta", "esse", "essa", "ao",
            "the", "is", "are", "in", "on", "at", "to", "and", "of", "a",
        }

        # Palavras relevantes para segurança
        security_keywords = {
            "pessoa", "pessoas", "homem", "mulher", "criança",
            "veículo", "carro", "moto", "caminhão", "bicicleta",
            "movimento", "entrando", "saindo", "correndo", "andando",
            "pacote", "mala", "bolsa", "objeto",
            "noite", "dia", "escuro", "iluminado",
            "suspeito", "alerta", "perigo", "emergência",
        }

        words = text.lower().split()
        keywords = []

        for word in words:
            # Remove pontuação
            word = "".join(c for c in word if c.isalnum())
            if word and word not in stop_words and len(word) > 2:
                if word in security_keywords or len(keywords) < 10:
                    if word not in keywords:
                        keywords.append(word)

        return keywords[:10]  # Limita a 10 keywords

    async def health_check(self) -> bool:
        """Verifica se o provedor está funcionando."""
        return True
