"""Modelo de câmera para captura de vídeo."""

import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional

from src.config import settings


class CameraStatus(str, Enum):
    """Status possíveis de uma câmera."""

    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    CAPTURING = "capturing"
    ERROR = "error"


@dataclass
class CameraConfig:
    """Configuração de uma câmera.

    frame_interval usa settings.frame_interval_seconds como valor padrão
    quando não especificado explicitamente.
    """

    id: uuid.UUID
    name: str
    url: str
    enabled: bool = True
    frame_interval: Optional[int] = None
    username: Optional[str] = None
    password: Optional[str] = None
    motion_detection_enabled: bool = True
    motion_threshold: float = 10.0
    motion_sensitivity: str = "medium"

    def __post_init__(self):
        if self.frame_interval is None:
            self.frame_interval = settings.frame_interval_seconds

    @property
    def rtsp_url(self) -> str:
        """Retorna a URL RTSP com credenciais se disponíveis."""
        if self.username and self.password:
            # Insere credenciais na URL RTSP
            if "://" in self.url:
                protocol, rest = self.url.split("://", 1)
                return f"{protocol}://{self.username}:{self.password}@{rest}"
        return self.url


@dataclass
class CameraState:
    """Estado atual de uma câmera."""

    config: CameraConfig
    status: CameraStatus = CameraStatus.DISCONNECTED
    last_frame_at: Optional[float] = None
    frames_captured: int = 0
    frames_sent: int = 0
    frames_filtered: int = 0
    errors_count: int = 0
    last_error: Optional[str] = None
    avg_motion_score: float = 0.0
    motion_score_sum: float = 0.0
    decoder_error_count: int = 0
    decoder_error_rate: float = 0.0
    last_decoder_error: Optional[str] = None

    @property
    def detection_rate(self) -> float:
        """Calcula taxa de detecção de movimento."""
        if self.frames_captured == 0:
            return 0.0
        return (self.frames_sent / self.frames_captured) * 100

    def reset_stats(self):
        """Reseta estatísticas."""
        self.frames_captured = 0
        self.frames_sent = 0
        self.frames_filtered = 0
        self.errors_count = 0
        self.last_error = None
        self.avg_motion_score = 0.0
        self.motion_score_sum = 0.0

    def record_frame(self, timestamp: float):
        """Registra captura de um frame."""
        self.last_frame_at = timestamp
        self.frames_captured += 1

    def record_sent_frame(self, motion_score: float):
        """Registra frame enviado para análise."""
        self.frames_sent += 1
        self.motion_score_sum += motion_score
        self.avg_motion_score = self.motion_score_sum / self.frames_sent

    def record_filtered_frame(self):
        """Registra frame filtrado."""
        self.frames_filtered += 1

    def record_error(self, error: str):
        """Registra um erro."""
        self.errors_count += 1
        self.last_error = error

    def record_decoder_error(self, error_msg: str = "H.264 decoder error"):
        """Registra um erro de decodificador."""
        self.decoder_error_count += 1
        self.last_decoder_error = error_msg
        self.decoder_error_rate = (
            self.decoder_error_count / self.frames_captured * 100
            if self.frames_captured > 0
            else 0.0
        )
