"""Testes para frame_interval e settings.frame_interval_seconds."""

import uuid
import asyncio
import pytest
from datetime import datetime

from src.config import settings
from src.capture.camera import CameraConfig
from src.api.schemas import CameraCreate, CameraUpdate
from sqlalchemy.ext.asyncio import AsyncSession


@pytest.mark.asyncio
async def test_camera_config_uses_settings_default():
    """Testa que CameraConfig usa settings.frame_interval_seconds como default."""
    config = CameraConfig(
        id=uuid.uuid4(),
        name="Test Camera",
        url="rtsp://test.com/stream",
    )
    
    assert config.frame_interval == settings.frame_interval_seconds


@pytest.mark.asyncio
async def test_camera_config_explicit_value_overrides_settings():
    """Testa que valor explícito sobrescreve settings."""
    explicit_interval = 999
    config = CameraConfig(
        id=uuid.uuid4(),
        name="Test Camera",
        url="rtsp://test.com/stream",
        frame_interval=explicit_interval,
    )
    
    assert config.frame_interval == explicit_interval


@pytest.mark.asyncio
async def test_camera_create_schema_uses_settings_default():
    """Testa que CameraCreate schema usa settings.frame_interval_seconds."""
    schema = CameraCreate(
        name="Test Camera",
        url="rtsp://test.com/stream",
    )
    
    assert schema.frame_interval == settings.frame_interval_seconds


@pytest.mark.asyncio
async def test_camera_update_schema_preserves_none():
    """Testa que CameraUpdate permite None (não altera valor existente)."""
    schema = CameraUpdate(
        name="Updated Name",
    )
    
    assert schema.frame_interval is None
    assert schema.name == "Updated Name"


@pytest.mark.asyncio
async def test_camera_create_with_explicit_interval(db_session: AsyncSession):
    """Testa criar câmera com intervalo explícito."""
    from src.storage.repository import CameraRepository
    
    repo = CameraRepository(db_session)
    camera = await repo.create(
        name="Test Camera Explicit",
        url="rtsp://test.com/stream",
        frame_interval=77,
    )
    
    assert camera.frame_interval == 77
    await db_session.rollback()


@pytest.mark.asyncio
async def test_camera_create_without_interval_uses_settings(db_session: AsyncSession):
    """Testa criar câmera sem intervalo usa settings."""
    from src.storage.repository import CameraRepository
    
    repo = CameraRepository(db_session)
    camera = await repo.create(
        name="Test Camera Default",
        url="rtsp://test.com/stream",
    )
    
    assert camera.frame_interval == settings.frame_interval_seconds
    await db_session.rollback()


@pytest.mark.asyncio
async def test_camera_update_does_not_change_interval_if_none(db_session: AsyncSession):
    """Testa que atualizar câmera sem frame_interval preserva valor existente."""
    from src.storage.repository import CameraRepository
    
    repo = CameraRepository(db_session)
    camera = await repo.create(
        name="Test Camera Update",
        url="rtsp://test.com/stream",
        frame_interval=55,
    )
    
    original_interval = camera.frame_interval
    
    # Atualiza sem especificar frame_interval
    updated = await repo.update(
        camera_id=camera.id,
        name="Updated Name",
    )
    
    assert updated.frame_interval == original_interval
    await db_session.rollback()


@pytest.mark.asyncio
async def test_camera_load_from_db_uses_stored_value(db_session: AsyncSession):
    """Testa que câmeras carregadas do banco usam valor armazenado."""
    from src.storage.repository import CameraRepository
    from src.capture.camera import CameraConfig
    
    repo = CameraRepository(db_session)
    
    # Cria câmera com intervalo específico
    camera = await repo.create(
        name="Test Camera Load",
        url="rtsp://test.com/stream",
        frame_interval=88,
    )
    
    # Carrega do banco
    loaded_camera = await repo.get_by_id(camera.id)
    assert loaded_camera.frame_interval == 88
    
    # Cria CameraConfig com valor do banco
    config = CameraConfig(
        id=loaded_camera.id,
        name=loaded_camera.name,
        url=loaded_camera.url,
        enabled=loaded_camera.enabled,
        frame_interval=loaded_camera.frame_interval,
    )
    
    assert config.frame_interval == 88
    await db_session.rollback()
