"""Rotas da API para câmeras.

Motion Detection Feature:
-----------------------
All cameras support motion detection to filter frames before LLM analysis:
- motion_detection_enabled: Enable/disable motion detection (default: true)
- motion_threshold: Motion percentage threshold 0-100 (default: 10.0)
  - Frames with motion_score < threshold are filtered
  - Static scenes typically see 80-90% API call reduction
  - Active scenes typically see 50-70% API call reduction

Camera Status includes:
- frames_sent: Frames sent to LLM (motion detected)
- frames_filtered: Frames dropped (no motion)
- detection_rate: % of frames sent (sent/captured * 100)
- avg_motion_score: Average motion score of sent frames

Stats Endpoint (/api/v1/stats):
- Aggregates motion metrics across all cameras
- motion_frames_total: Total frames captured
- motion_frames_sent: Total sent to LLM
- motion_frames_filtered: Total filtered
- motion_detection_rate: Overall detection rate (%)
"""

import uuid
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.storage import get_db, CameraRepository
from src.api.schemas import (
    CameraCreate,
    CameraUpdate,
    CameraResponse,
    CameraStatusResponse,
)
import os

router = APIRouter(prefix="/cameras", tags=["Câmeras"])


def detect_source_type(url: str) -> str:
    """Auto-detect source type from URL."""
    if url.startswith("rtsp://") or url.startswith("rtmp://"):
        return "rtsp"
    elif os.path.exists(os.path.expandvars(url)):
        return "video_file"
    else:
        return "rtsp"  # Default to rtsp for unknown URLs


def validate_video_file(url: str, source_type: Optional[str]) -> tuple[bool, str]:
    """Validate video file exists and is readable."""
    if not source_type or source_type != "video_file":
        return True, ""

    expanded_path = os.path.expandvars(url)
    abs_path = os.path.abspath(expanded_path)

    # Check if file exists
    if not os.path.exists(abs_path):
        return False, f"Video file not found: {abs_path}"

    # Check file extension
    supported_extensions = {".mp4", ".avi", ".mov", ".mkv", ".webm", ".flv", ".m4v"}
    _, ext = os.path.splitext(abs_path)
    if ext.lower() not in supported_extensions:
        return (
            False,
            f"Unsupported video format: {ext}. Supported: {', '.join(supported_extensions)}",
        )

    return True, ""

    expanded_path = os.path.expandvars(url)
    abs_path = os.path.abspath(expanded_path)

    # Check if file exists
    if not os.path.exists(abs_path):
        return False, f"Video file not found: {abs_path}"

    # Check file extension
    supported_extensions = {".mp4", ".avi", ".mov", ".mkv", ".webm", ".flv", ".m4v"}
    _, ext = os.path.splitext(abs_path)
    if ext.lower() not in supported_extensions:
        return (
            False,
            f"Unsupported video format: {ext}. Supported: {', '.join(supported_extensions)}",
        )

    return True, ""


@router.get("", response_model=List[CameraResponse])
async def list_cameras(
    enabled_only: bool = False,
    db: AsyncSession = Depends(get_db),
):
    """Lista todas as câmeras."""
    repo = CameraRepository(db)
    cameras = await repo.get_all(enabled_only=enabled_only)
    return cameras


@router.post("", response_model=CameraResponse, status_code=status.HTTP_201_CREATED)
async def create_camera(
    camera: CameraCreate,
    db: AsyncSession = Depends(get_db),
):
    """Cria uma nova câmera."""
    # Auto-detect source type if not provided
    source_type = camera.source_type
    if not source_type or source_type == "rtsp":
        source_type = detect_source_type(camera.url)

    # Validate video file if source_type is video_file
    is_valid, error_msg = validate_video_file(camera.url, source_type)
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_msg,
        )

    repo = CameraRepository(db)
    new_camera = await repo.create(
        name=camera.name,
        url=camera.url,
        source_type=source_type,
        enabled=camera.enabled,
        frame_interval=camera.frame_interval,
        motion_detection_enabled=camera.motion_detection_enabled,
        motion_threshold=camera.motion_threshold,
        motion_sensitivity=camera.motion_sensitivity,
    )
    return new_camera


@router.get("/{camera_id}", response_model=CameraResponse)
async def get_camera(
    camera_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """Obtém detalhes de uma câmera."""
    repo = CameraRepository(db)
    camera = await repo.get_by_id(camera_id)
    if not camera:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Câmera não encontrada",
        )
    return camera


@router.put("/{camera_id}", response_model=CameraResponse)
async def update_camera(
    camera_id: uuid.UUID,
    camera: CameraUpdate,
    db: AsyncSession = Depends(get_db),
):
    """Atualiza uma câmera."""
    # Detect source type if URL is being updated
    source_type = camera.source_type
    if camera.url and (not source_type or source_type == "rtsp"):
        source_type = detect_source_type(camera.url)

    # Validate video file if source type is video_file
    if camera.url:
        is_valid, error_msg = validate_video_file(camera.url, source_type)
        if not is_valid:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error_msg,
            )

    repo = CameraRepository(db)
    updated = await repo.update(
        camera_id=camera_id,
        name=camera.name,
        url=camera.url,
        source_type=source_type,
        enabled=camera.enabled,
        frame_interval=camera.frame_interval,
        motion_detection_enabled=camera.motion_detection_enabled,
        motion_threshold=camera.motion_threshold,
        motion_sensitivity=camera.motion_sensitivity,
    )
    if not updated:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Câmera não encontrada",
        )
    return updated


@router.delete("/{camera_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_camera(
    camera_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """Remove uma câmera."""
    repo = CameraRepository(db)
    deleted = await repo.delete(camera_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Câmera não encontrada",
        )


@router.post("/{camera_id}/start", status_code=status.HTTP_200_OK)
async def start_camera(
    camera_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """Inicia a captura de uma câmera."""
    # Importa aqui para evitar circular import
    from src.main import camera_manager
    from src.capture import CameraConfig

    repo = CameraRepository(db)
    camera = await repo.get_by_id(camera_id)
    if not camera:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Câmera não encontrada no banco de dados",
        )

    try:
        # Adiciona a câmera ao manager se ainda não estiver
        config = CameraConfig(
            id=camera.id,
            name=camera.name,
            url=camera.url,
            source_type=getattr(camera, "source_type", "rtsp"),
            enabled=camera.enabled,
            frame_interval=camera.frame_interval,
            motion_detection_enabled=camera.motion_detection_enabled,
            motion_threshold=camera.motion_threshold,
            motion_sensitivity=camera.motion_sensitivity
            if hasattr(camera, "motion_sensitivity")
            else "medium",
        )
        await camera_manager.add_camera(config)

        # Inicia a captura
        await camera_manager.start_camera(camera_id)
        return {"message": f"Captura iniciada para câmera {camera.name}"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )


@router.post("/{camera_id}/stop", status_code=status.HTTP_200_OK)
async def stop_camera(
    camera_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """Para a captura de uma câmera."""
    from src.main import camera_manager

    repo = CameraRepository(db)
    camera = await repo.get_by_id(camera_id)
    if not camera:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Câmera não encontrada",
        )

    try:
        await camera_manager.stop_camera(camera_id)
        return {"message": f"Captura parada para câmera {camera.name}"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )


@router.get("/{camera_id}/status", response_model=CameraStatusResponse)
async def get_camera_status(
    camera_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """Obtém o status de captura de uma câmera."""
    from src.main import camera_manager

    repo = CameraRepository(db)
    camera = await repo.get_by_id(camera_id)
    if not camera:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Câmera não encontrada",
        )

    status_info = camera_manager.get_camera_status(camera_id)
    if not status_info:
        return CameraStatusResponse(
            id=camera_id,
            name=camera.name,
            status="not_started",
            frames_captured=0,
            frames_sent=0,
            frames_filtered=0,
            detection_rate=0.0,
            avg_motion_score=0.0,
            last_frame_at=None,
            errors_count=0,
            last_error=None,
            decoder_error_count=0,
            decoder_error_rate=0.0,
            last_decoder_error=None,
            initial_frames_discarded=0,
            current_frame_number=0,
            total_frames=0,
            progress_percentage=0.0,
            source_type=camera.source_type
            if hasattr(camera, "source_type")
            else "rtsp",
        )

    return CameraStatusResponse(
        id=camera_id,
        name=camera.name,
        frames_sent=status_info.get("frames_sent", 0),
        frames_filtered=status_info.get("frames_filtered", 0),
        detection_rate=status_info.get("detection_rate", 0.0),
        avg_motion_score=status_info.get("avg_motion_score", 0.0),
        current_frame_number=status_info.get("current_frame_number", 0),
        total_frames=status_info.get("total_frames", 0),
        progress_percentage=status_info.get("progress_percentage", 0.0),
        source_type=status_info.get(
            "source_type",
            camera.source_type if hasattr(camera, "source_type") else "rtsp",
        ),
        **status_info,
    )
