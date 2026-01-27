"""Modelos SQLAlchemy para o CamOpsAI."""

import uuid
from datetime import datetime
from typing import List, Optional

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, String, Text, Integer
from sqlalchemy.dialects.postgresql import ARRAY, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .database import Base


class Camera(Base):
    """Modelo para câmeras IP."""

    __tablename__ = "cameras"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    url: Mapped[str] = mapped_column(String(512), nullable=False)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    frame_interval: Mapped[int] = mapped_column(Integer, nullable=False)
    motion_detection_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    motion_threshold: Mapped[float] = mapped_column(Float, default=10.0)
    motion_sensitivity: Mapped[str] = mapped_column(String(20), default="medium")
    decoder_error_count: Mapped[int] = mapped_column(Integer, default=0)
    decoder_error_rate: Mapped[float] = mapped_column(Float, default=0.0)
    last_decoder_error: Mapped[Optional[str]] = mapped_column(
        String(255), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # Relacionamentos
    events: Mapped[List["Event"]] = relationship(
        "Event", back_populates="camera", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Camera(id={self.id}, name={self.name})>"


class Event(Base):
    """Modelo para eventos detectados."""

    __tablename__ = "events"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    camera_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("cameras.id"), nullable=False
    )
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    keywords: Mapped[Optional[List[str]]] = mapped_column(ARRAY(String), nullable=True)
    frame_path: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    confidence: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    llm_provider: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    llm_model: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    processing_time_ms: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    # Relacionamentos
    camera: Mapped["Camera"] = relationship("Camera", back_populates="events")
    alert_logs: Mapped[List["AlertLog"]] = relationship(
        "AlertLog", back_populates="event", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Event(id={self.id}, camera_id={self.camera_id})>"


class AlertRule(Base):
    """Modelo para regras de alerta."""

    __tablename__ = "alert_rules"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    keywords: Mapped[List[str]] = mapped_column(ARRAY(String), nullable=False)
    camera_ids: Mapped[Optional[List[str]]] = mapped_column(
        ARRAY(String), nullable=True
    )  # None = todas as câmeras
    phone_numbers: Mapped[List[str]] = mapped_column(ARRAY(String), nullable=False)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    priority: Mapped[str] = mapped_column(String(20), default="normal")
    cooldown_seconds: Mapped[int] = mapped_column(
        Integer, default=300
    )  # 5 minutos entre alertas
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # Relacionamentos
    alert_logs: Mapped[List["AlertLog"]] = relationship(
        "AlertLog", back_populates="alert_rule", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<AlertRule(id={self.id}, name={self.name})>"


class AlertLog(Base):
    """Modelo para histórico de alertas enviados."""

    __tablename__ = "alert_logs"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    event_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("events.id"), nullable=False
    )
    alert_rule_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("alert_rules.id"), nullable=False
    )
    keywords_matched: Mapped[List[str]] = mapped_column(ARRAY(String), nullable=False)
    sent_to: Mapped[List[str]] = mapped_column(ARRAY(String), nullable=False)
    sent_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    status: Mapped[str] = mapped_column(String(20), default="pending")
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Relacionamentos
    event: Mapped["Event"] = relationship("Event", back_populates="alert_logs")
    alert_rule: Mapped["AlertRule"] = relationship(
        "AlertRule", back_populates="alert_logs"
    )

    def __repr__(self) -> str:
        return f"<AlertLog(id={self.id}, status={self.status})>"
