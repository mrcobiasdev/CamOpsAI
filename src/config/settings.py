"""Configurações do CamOpsAI usando Pydantic Settings."""

from enum import Enum
from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class LLMProvider(str, Enum):
    """Provedores de LLM suportados."""

    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GEMINI = "gemini"
    LMSTUDIO = "lmstudio"


class WhatsAppSendMode(str, Enum):
    """Modos de envio do WhatsApp."""

    API = "api"
    WEB = "web"


class Settings(BaseSettings):
    """Configurações da aplicação."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # Banco de Dados
    database_url: str = Field(
        default="postgresql+asyncpg://user:password@localhost:5432/camopsai",
        description="URL de conexão com o PostgreSQL",
    )

    # Provedor LLM
    llm_provider: LLMProvider = Field(
        default=LLMProvider.OPENAI,
        description="Provedor de LLM para análise de imagens",
    )

    # OpenAI
    openai_api_key: Optional[str] = Field(
        default=None, description="Chave da API OpenAI"
    )
    openai_model: str = Field(default="gpt-4o", description="Modelo OpenAI")

    # Anthropic
    anthropic_api_key: Optional[str] = Field(
        default=None, description="Chave da API Anthropic"
    )
    anthropic_model: str = Field(
        default="claude-sonnet-4-20250514", description="Modelo Anthropic"
    )

    # Google Gemini
    gemini_api_key: Optional[str] = Field(
        default=None, description="Chave da API Gemini"
    )
    gemini_model: str = Field(default="gemini-pro-vision", description="Modelo Gemini")

    # LM Studio (modelo local)
    lmstudio_api_url: str = Field(
        default="http://localhost:1234/v1", description="URL da API LM Studio"
    )
    lmstudio_model: str = Field(default="local-model", description="Modelo LM Studio")

    # WhatsApp
    whatsapp_send_mode: WhatsAppSendMode = Field(
        default=WhatsAppSendMode.API,
        description="Modo de envio do WhatsApp (api ou web)",
    )
    whatsapp_api_url: str = Field(default="https://graph.facebook.com/v18.0")
    whatsapp_token: Optional[str] = Field(default=None)
    whatsapp_phone_id: Optional[str] = Field(default=None)
    whatsapp_session_dir: str = Field(
        default="./sessions/whatsapp/",
        description="Diretório para salvar sessão do WhatsApp Web",
    )
    whatsapp_headless: bool = Field(
        default=True,
        description="Executar navegador em modo headless para WhatsApp Web",
    )

    # Processamento
    frame_interval_seconds: int = Field(default=10, ge=1)
    frames_storage_path: str = Field(default="./frames")
    max_queue_size: int = Field(default=100, ge=10)
    motion_detection_enabled: bool = Field(default=True)
    motion_threshold: float = Field(default=10.0, ge=0.0, le=100.0)

    # API
    api_host: str = Field(default="0.0.0.0")
    api_port: int = Field(default=8000, ge=1, le=65535)
    debug: bool = Field(default=False)

    # Logging
    log_level: str = Field(default="INFO")

    # RTSP Configuration
    rtsp_transport: str = Field(
        default="tcp", description="RTSP transport protocol (tcp/udp)"
    )
    rtsp_error_recovery: bool = Field(
        default=True, description="Enable error recovery for RTSP streams"
    )
    rtsp_max_consecutive_errors: int = Field(
        default=10, ge=1, le=100, description="Max consecutive errors before reconnect"
    )
    initial_frames_to_discard: int = Field(
        default=5,
        ge=0,
        description="Number of initial frames to discard after connection",
    )

    def get_llm_api_key(self) -> Optional[str]:
        """Retorna a chave da API do provedor LLM configurado."""
        keys = {
            LLMProvider.OPENAI: self.openai_api_key,
            LLMProvider.ANTHROPIC: self.anthropic_api_key,
            LLMProvider.GEMINI: self.gemini_api_key,
            LLMProvider.LMSTUDIO: "lmstudio",  # placeholder, não precisa de key real
        }
        return keys.get(self.llm_provider)

    def get_llm_model(self) -> str:
        """Retorna o modelo do provedor LLM configurado."""
        models = {
            LLMProvider.OPENAI: self.openai_model,
            LLMProvider.ANTHROPIC: self.anthropic_model,
            LLMProvider.GEMINI: self.gemini_model,
            LLMProvider.LMSTUDIO: self.lmstudio_model,
        }
        return models.get(self.llm_provider, self.openai_model)


settings = Settings()
