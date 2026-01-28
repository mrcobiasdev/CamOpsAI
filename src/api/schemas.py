"""Schemas Pydantic para a API."""

import uuid
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field

from src.config import settings


# ==================== Camera Schemas ====================


class CameraBase(BaseModel):
    """Schema base para câmera.

    frame_interval usa settings.frame_interval_seconds como valor padrão
    quando não especificado.
    """

    name: str = Field(..., min_length=1, max_length=255)
    url: str = Field(..., min_length=1, max_length=512)
    enabled: bool = True
    frame_interval: int = Field(
        default_factory=lambda: settings.frame_interval_seconds, ge=1, le=3600
    )
    motion_detection_enabled: bool = True
    motion_threshold: float = Field(default=10.0, ge=0.0, le=100.0)
    motion_sensitivity: str = Field(
        default="medium", pattern="^(low|medium|high|custom)$"
    )


class CameraCreate(CameraBase):
    """Schema para criação de câmera."""

    pass


class CameraUpdate(BaseModel):
    """Schema para atualização de câmera."""

    name: Optional[str] = Field(None, min_length=1, max_length=255)
    url: Optional[str] = Field(None, min_length=1, max_length=512)
    enabled: Optional[bool] = None
    frame_interval: Optional[int] = Field(None, ge=1, le=3600)
    motion_detection_enabled: Optional[bool] = None
    motion_threshold: Optional[float] = Field(None, ge=0.0, le=100.0)
    motion_sensitivity: Optional[str] = Field(
        None, pattern="^(low|medium|high|custom)$"
    )


class CameraResponse(CameraBase):
    """Schema de resposta para câmera."""

    id: uuid.UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class CameraStatusResponse(BaseModel):
    """Schema para status de câmera."""

    id: uuid.UUID
    name: str
    status: str
    frames_captured: int
    frames_sent: int
    frames_filtered: int
    detection_rate: float
    avg_motion_score: float
    last_frame_at: Optional[datetime]
    errors_count: int
    last_error: Optional[str]
    decoder_error_count: int
    decoder_error_rate: float
    last_decoder_error: Optional[str]
    initial_frames_discarded: int


# ==================== Event Schemas ====================


class EventBase(BaseModel):
    """Schema base para evento."""

    camera_id: uuid.UUID
    description: str
    keywords: Optional[List[str]] = None
    confidence: Optional[float] = None


class EventCreate(EventBase):
    """Schema para criação de evento."""

    frame_path: Optional[str] = None
    annotated_frame_path: Optional[str] = None
    llm_provider: Optional[str] = None
    llm_model: Optional[str] = None
    processing_time_ms: Optional[int] = None


class EventResponse(EventBase):
    """Schema de resposta para evento."""

    id: uuid.UUID
    timestamp: datetime
    frame_path: Optional[str]
    annotated_frame_path: Optional[str] = None
    annotated_frame_url: Optional[str] = None
    llm_provider: Optional[str]
    llm_model: Optional[str]
    processing_time_ms: Optional[int]

    class Config:
        from_attributes = True


class EventListResponse(BaseModel):
    """Schema para listagem de eventos."""

    events: List[EventResponse]
    total: int
    page: int
    page_size: int


class TimelineResponse(BaseModel):
    """Schema para timeline de eventos."""

    events: List[EventResponse]
    start_date: Optional[datetime]
    end_date: Optional[datetime]


# ==================== Alert Schemas ====================


class AlertRuleBase(BaseModel):
    """Schema base para regra de alerta."""

    name: str = Field(..., min_length=1, max_length=255)
    keywords: List[str] = Field(..., min_items=1)
    phone_numbers: List[str] = Field(..., min_items=1)
    camera_ids: Optional[List[str]] = None
    enabled: bool = True
    priority: str = Field(default="normal", pattern="^(low|normal|high)$")
    cooldown_seconds: int = Field(default=300, ge=0)


class AlertRuleCreate(AlertRuleBase):
    """Schema para criação de regra de alerta."""

    pass


class AlertRuleUpdate(BaseModel):
    """Schema para atualização de regra de alerta."""

    name: Optional[str] = Field(None, min_length=1, max_length=255)
    keywords: Optional[List[str]] = Field(None, min_items=1)
    phone_numbers: Optional[List[str]] = Field(None, min_items=1)
    camera_ids: Optional[List[str]] = None
    enabled: Optional[bool] = None
    priority: Optional[str] = Field(None, pattern="^(low|normal|high)$")
    cooldown_seconds: Optional[int] = Field(None, ge=0)


class AlertRuleResponse(AlertRuleBase):
    """Schema de resposta para regra de alerta."""

    id: uuid.UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class AlertLogResponse(BaseModel):
    """Schema de resposta para log de alerta."""

    id: uuid.UUID
    event_id: uuid.UUID
    alert_rule_id: uuid.UUID
    keywords_matched: List[str]
    sent_to: List[str]
    sent_at: datetime
    status: str
    error_message: Optional[str]

    class Config:
        from_attributes = True


class AlertLogListResponse(BaseModel):
    """Schema para listagem de logs de alerta."""

    logs: List[AlertLogResponse]
    total: int
    page: int
    page_size: int


# ==================== System Schemas ====================


class HealthResponse(BaseModel):
    """Schema para health check."""

    status: str
    database: bool
    llm_provider: Optional[dict]
    whatsapp: bool
    version: str


class StatsResponse(BaseModel):
    """Schema para estatísticas do sistema."""

    cameras_total: int
    cameras_active: int
    events_total: int
    events_today: int
    alerts_sent_total: int
    alerts_sent_today: int
    queue_size: int
    queue_processed: int
    queue_dropped: int
    # Motion detection metrics
    motion_frames_total: int = 0
    motion_frames_sent: int = 0
    motion_frames_filtered: int = 0
    motion_detection_rate: float = 0.0

    # Decoder health metrics
    decoder_total_errors: int = 0
    decoder_avg_error_rate: float = 0.0


class ErrorResponse(BaseModel):
    """Schema para resposta de erro."""

    detail: str
    error_code: Optional[str] = None
