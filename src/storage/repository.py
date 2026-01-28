"""Repositórios para operações CRUD no banco de dados."""

import uuid
from datetime import datetime
from typing import List, Optional

from sqlalchemy import select, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession

from .models import Camera, Event, AlertRule, AlertLog
from src.config import settings


class CameraRepository:
    """Repositório para operações com câmeras."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(
        self,
        name: str,
        url: str,
        enabled: bool = True,
        frame_interval: Optional[int] = None,
        motion_detection_enabled: Optional[bool] = None,
        motion_threshold: Optional[float] = None,
        motion_sensitivity: Optional[str] = None,
    ) -> Camera:
        """Cria uma nova câmera.

        Se frame_interval não for especificado, usa settings.frame_interval_seconds.
        Se motion_detection_enabled não for especificado, usa settings.motion_detection_enabled.
        Se motion_threshold não for especificado, usa settings.motion_threshold.
        Se motion_sensitivity não for especificado, usa 'medium'.
        """
        if frame_interval is None:
            frame_interval = settings.frame_interval_seconds
        if motion_detection_enabled is None:
            motion_detection_enabled = settings.motion_detection_enabled
        if motion_threshold is None:
            motion_threshold = settings.motion_threshold
        if motion_sensitivity is None:
            motion_sensitivity = "medium"

        camera = Camera(
            name=name,
            url=url,
            enabled=enabled,
            frame_interval=frame_interval,
            motion_detection_enabled=motion_detection_enabled,
            motion_threshold=motion_threshold,
            motion_sensitivity=motion_sensitivity,
        )
        self.session.add(camera)
        await self.session.commit()
        return camera

    async def get_by_id(self, camera_id: uuid.UUID) -> Optional[Camera]:
        """Busca câmera por ID."""
        result = await self.session.execute(
            select(Camera).where(Camera.id == camera_id)
        )
        return result.scalar_one_or_none()

    async def get_all(self, enabled_only: bool = False) -> List[Camera]:
        """Lista todas as câmeras."""
        query = select(Camera)
        if enabled_only:
            query = query.where(Camera.enabled == True)
        query = query.order_by(Camera.name)
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def update(
        self,
        camera_id: uuid.UUID,
        name: Optional[str] = None,
        url: Optional[str] = None,
        enabled: Optional[bool] = None,
        frame_interval: Optional[int] = None,
        motion_detection_enabled: Optional[bool] = None,
        motion_threshold: Optional[float] = None,
        motion_sensitivity: Optional[str] = None,
    ) -> Optional[Camera]:
        """Atualiza uma câmera."""
        camera = await self.get_by_id(camera_id)
        if not camera:
            return None

        if name is not None:
            camera.name = name
        if url is not None:
            camera.url = url
        if enabled is not None:
            camera.enabled = enabled
        if frame_interval is not None:
            camera.frame_interval = frame_interval
        if motion_detection_enabled is not None:
            camera.motion_detection_enabled = motion_detection_enabled
        if motion_threshold is not None:
            camera.motion_threshold = motion_threshold
        if motion_sensitivity is not None:
            camera.motion_sensitivity = motion_sensitivity

        await self.session.commit()
        return camera

    async def update_decoder_stats(
        self,
        camera_id: uuid.UUID,
        decoder_error_count: int,
        decoder_error_rate: float,
        last_decoder_error: Optional[str] = None,
    ) -> Optional[Camera]:
        """Atualiza estatísticas de decoder de uma câmera."""
        camera = await self.get_by_id(camera_id)
        if not camera:
            return None

        camera.decoder_error_count = decoder_error_count
        camera.decoder_error_rate = decoder_error_rate
        camera.last_decoder_error = last_decoder_error

        await self.session.commit()
        return camera

    async def delete(self, camera_id: uuid.UUID) -> bool:
        """Remove uma câmera."""
        camera = await self.get_by_id(camera_id)
        if not camera:
            return False
        await self.session.delete(camera)
        await self.session.commit()
        return True


class EventRepository:
    """Repositório para operações com eventos."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(
        self,
        camera_id: uuid.UUID,
        description: str,
        keywords: Optional[List[str]] = None,
        frame_path: Optional[str] = None,
        annotated_frame_path: Optional[str] = None,
        confidence: Optional[float] = None,
        llm_provider: Optional[str] = None,
        llm_model: Optional[str] = None,
        processing_time_ms: Optional[int] = None,
    ) -> Event:
        """Cria um novo evento."""
        event = Event(
            camera_id=camera_id,
            description=description,
            keywords=keywords,
            frame_path=frame_path,
            annotated_frame_path=annotated_frame_path,
            confidence=confidence,
            llm_provider=llm_provider,
            llm_model=llm_model,
            processing_time_ms=processing_time_ms,
        )
        self.session.add(event)
        await self.session.commit()
        return event

    async def get_by_id(self, event_id: uuid.UUID) -> Optional[Event]:
        """Busca evento por ID."""
        result = await self.session.execute(select(Event).where(Event.id == event_id))
        return result.scalar_one_or_none()

    async def get_by_camera(
        self,
        camera_id: uuid.UUID,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[Event]:
        """Lista eventos de uma câmera."""
        query = select(Event).where(Event.camera_id == camera_id)

        if start_date:
            query = query.where(Event.timestamp >= start_date)
        if end_date:
            query = query.where(Event.timestamp <= end_date)

        query = query.order_by(Event.timestamp.desc()).limit(limit).offset(offset)
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def search_by_keyword(
        self,
        keyword: str,
        camera_id: Optional[uuid.UUID] = None,
        limit: int = 100,
    ) -> List[Event]:
        """Busca eventos por palavra-chave."""
        query = select(Event).where(Event.keywords.contains([keyword]))

        if camera_id:
            query = query.where(Event.camera_id == camera_id)

        query = query.order_by(Event.timestamp.desc()).limit(limit)
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_timeline(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        camera_ids: Optional[List[uuid.UUID]] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[Event]:
        """Retorna timeline de eventos."""
        query = select(Event)

        conditions = []
        if start_date:
            conditions.append(Event.timestamp >= start_date)
        if end_date:
            conditions.append(Event.timestamp <= end_date)
        if camera_ids:
            conditions.append(Event.camera_id.in_(camera_ids))

        if conditions:
            query = query.where(and_(*conditions))

        query = query.order_by(Event.timestamp.desc()).limit(limit).offset(offset)
        result = await self.session.execute(query)
        return list(result.scalars().all())


class AlertRepository:
    """Repositório para operações com alertas."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_rule(
        self,
        name: str,
        keywords: List[str],
        phone_numbers: List[str],
        camera_ids: Optional[List[str]] = None,
        enabled: bool = True,
        priority: str = "normal",
        cooldown_seconds: int = 300,
    ) -> AlertRule:
        """Cria uma nova regra de alerta."""
        rule = AlertRule(
            name=name,
            keywords=keywords,
            phone_numbers=phone_numbers,
            camera_ids=camera_ids,
            enabled=enabled,
            priority=priority,
            cooldown_seconds=cooldown_seconds,
        )
        self.session.add(rule)
        await self.session.commit()
        return rule

    async def get_rule_by_id(self, rule_id: uuid.UUID) -> Optional[AlertRule]:
        """Busca regra por ID."""
        result = await self.session.execute(
            select(AlertRule).where(AlertRule.id == rule_id)
        )
        return result.scalar_one_or_none()

    async def get_all_rules(self, enabled_only: bool = False) -> List[AlertRule]:
        """Lista todas as regras de alerta."""
        query = select(AlertRule)
        if enabled_only:
            query = query.where(AlertRule.enabled == True)
        query = query.order_by(AlertRule.name)
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_rules_for_camera(self, camera_id: uuid.UUID) -> List[AlertRule]:
        """Busca regras aplicáveis a uma câmera."""
        result = await self.session.execute(
            select(AlertRule).where(
                and_(
                    AlertRule.enabled == True,
                    or_(
                        AlertRule.camera_ids == None,
                        AlertRule.camera_ids.contains([str(camera_id)]),
                    ),
                )
            )
        )
        return list(result.scalars().all())

    async def update_rule(
        self,
        rule_id: uuid.UUID,
        name: Optional[str] = None,
        keywords: Optional[List[str]] = None,
        phone_numbers: Optional[List[str]] = None,
        camera_ids: Optional[List[str]] = None,
        enabled: Optional[bool] = None,
        priority: Optional[str] = None,
        cooldown_seconds: Optional[int] = None,
    ) -> Optional[AlertRule]:
        """Atualiza uma regra de alerta."""
        rule = await self.get_rule_by_id(rule_id)
        if not rule:
            return None

        if name is not None:
            rule.name = name
        if keywords is not None:
            rule.keywords = keywords
        if phone_numbers is not None:
            rule.phone_numbers = phone_numbers
        if camera_ids is not None:
            rule.camera_ids = camera_ids
        if enabled is not None:
            rule.enabled = enabled
        if priority is not None:
            rule.priority = priority
        if cooldown_seconds is not None:
            rule.cooldown_seconds = cooldown_seconds

        await self.session.commit()
        return rule

    async def delete_rule(self, rule_id: uuid.UUID) -> bool:
        """Remove uma regra de alerta."""
        rule = await self.get_rule_by_id(rule_id)
        if not rule:
            return False
        await self.session.delete(rule)
        await self.session.commit()
        return True

    async def create_log(
        self,
        event_id: uuid.UUID,
        alert_rule_id: uuid.UUID,
        keywords_matched: List[str],
        sent_to: List[str],
        status: str = "pending",
        error_message: Optional[str] = None,
    ) -> AlertLog:
        """Cria um registro de alerta enviado."""
        log = AlertLog(
            event_id=event_id,
            alert_rule_id=alert_rule_id,
            keywords_matched=keywords_matched,
            sent_to=sent_to,
            status=status,
            error_message=error_message,
        )
        self.session.add(log)
        await self.session.commit()
        return log

    async def get_logs(
        self,
        rule_id: Optional[uuid.UUID] = None,
        status: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[AlertLog]:
        """Lista histórico de alertas."""
        query = select(AlertLog)

        conditions = []
        if rule_id:
            conditions.append(AlertLog.alert_rule_id == rule_id)
        if status:
            conditions.append(AlertLog.status == status)

        if conditions:
            query = query.where(and_(*conditions))

        query = query.order_by(AlertLog.sent_at.desc()).limit(limit).offset(offset)
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def update_log_status(
        self,
        log_id: uuid.UUID,
        status: str,
        error_message: Optional[str] = None,
    ) -> Optional[AlertLog]:
        """Atualiza status de um log de alerta."""
        result = await self.session.execute(
            select(AlertLog).where(AlertLog.id == log_id)
        )
        log = result.scalar_one_or_none()
        if not log:
            return None

        log.status = status
        if error_message:
            log.error_message = error_message

        await self.session.commit()
        return log
