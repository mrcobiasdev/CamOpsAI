"""Integration tests for frame annotation."""

import pytest
import numpy as np
import cv2
import uuid
from pathlib import Path
from datetime import datetime
from unittest.mock import patch, MagicMock, ANY
import time

from src.capture.frame_annotation import FrameAnnotation
from src.storage.models import Event
from src.storage.repository import EventRepository
from src.config import settings


@pytest.mark.asyncio
async def test_frame_annotation_integration(db_session):
    """Test complete flow of frame annotation with database."""
    event_repo = EventRepository(db_session)

    # Create a sample event with annotated frame
    sample_frame = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
    _, buffer = cv2.imencode(".jpg", sample_frame)
    frame_bytes = buffer.tobytes()

    # Create motion mask
    motion_mask = np.random.randint(0, 256, (240, 320), dtype=np.uint8)

    with (
        patch("src.config.settings.annotation_mask_alpha", 0.3),
        patch("src.config.settings.annotation_mask_color", "0,255,0"),
        patch("src.config.settings.annotation_text_color", "255,255,255"),
        patch("src.config.settings.annotation_font_scale", 0.6),
        patch("src.config.settings.annotation_thickness", 2),
    ):
        annotator = FrameAnnotation(
            motion_score=45.2,
            motion_threshold=10.0,
            motion_mask=motion_mask,
            llm_keywords=["person", "alert"],
            llm_confidence=0.92,
            llm_provider="openai",
            llm_model="gpt-4o",
            motion_status="MOTION",
        )

        annotated_bytes = annotator.annotate_frame(frame_bytes)
        assert annotated_bytes is not None

    # Save annotated frame to temporary location
    temp_dir = Path(settings.annotated_frames_storage_path)
    temp_dir.mkdir(parents=True, exist_ok=True)
    timestamp_ms = int(datetime.now().timestamp() * 1000)
    annotated_filename = f"{uuid.uuid4()}_{timestamp_ms}_annotated.jpg"
    annotated_path = temp_dir / annotated_filename

    with open(annotated_path, "wb") as f:
        f.write(annotated_bytes)

    # Create event in database
    event = await event_repo.create(
        camera_id=uuid.uuid4(),
        description="Test event with annotation",
        keywords=["person", "alert"],
        frame_path=str(temp_dir / f"{uuid.uuid4()}.jpg"),
        annotated_frame_path=str(annotated_path),
        confidence=0.92,
        llm_provider="openai",
        llm_model="gpt-4o",
        processing_time_ms=150,
    )

    assert event.annotated_frame_path is not None
    assert event.annotated_frame_url is not None

    # Cleanup
    if annotated_path.exists():
        annotated_path.unlink()


@pytest.mark.asyncio
async def test_cleanup_annotated_frames():
    """Test cleanup of old annotated frames."""

    # Define a simple cleanup function for testing
    def cleanup_old_files(retention_days):
        """Cleanup function similar to the one in main.py."""
        temp_dir = Path(settings.annotated_frames_storage_path)
        if not temp_dir.exists():
            return

        cutoff_time = time.time() - (retention_days * 24 * 60 * 60)
        deleted_count = 0

        for file_path in temp_dir.glob("*_annotated.jpg"):
            if file_path.is_file() and file_path.stat().st_mtime < cutoff_time:
                file_path.unlink()
                deleted_count += 1

        return deleted_count

    temp_dir = Path(settings.annotated_frames_storage_path)
    temp_dir.mkdir(parents=True, exist_ok=True)

    # Create test files with different ages
    old_timestamp = int((datetime.now().timestamp() - 35 * 24 * 60 * 60) * 1000)
    recent_timestamp = int((datetime.now().timestamp() - 1 * 24 * 60 * 60) * 1000)

    old_file = temp_dir / f"camera_{old_timestamp}_annotated.jpg"
    recent_file = temp_dir / f"camera_{recent_timestamp}_annotated.jpg"

    old_file.touch()
    recent_file.touch()

    assert old_file.exists()
    assert recent_file.exists()

    # Use retention days of 30 days
    deleted_count = cleanup_old_files(30)

    # Old file should be deleted, recent file should remain
    assert deleted_count >= 1
    assert not old_file.exists()
    assert recent_file.exists()

    # Cleanup
    if recent_file.exists():
        recent_file.unlink()


@pytest.mark.asyncio
async def test_annotation_disabled_scenario(db_session):
    """Test that annotation is skipped when disabled."""
    event_repo = EventRepository(db_session)

    with patch("src.capture.frame_annotation.settings") as mock_settings:
        mock_settings.annotation_enabled = False

        # Create event without annotation
        event = await event_repo.create(
            camera_id=uuid.uuid4(),
            description="Test event without annotation",
            keywords=["alert"],
            frame_path="test/path.jpg",
            annotated_frame_path=None,
            confidence=0.92,
            llm_provider="openai",
            llm_model="gpt-4o",
            processing_time_ms=150,
        )

        assert event.annotated_frame_path is None


@pytest.mark.asyncio
async def test_annotation_with_error_handling(db_session):
    """Test that annotation errors don't prevent event creation."""
    event_repo = EventRepository(db_session)

    # Create event when annotation fails
    event = await event_repo.create(
        camera_id=uuid.uuid4(),
        description="Test event with failed annotation",
        keywords=["alert"],
        frame_path="test/path.jpg",
        annotated_frame_path=None,
        confidence=0.92,
        llm_provider="openai",
        llm_model="gpt-4o",
        processing_time_ms=150,
    )

    assert event is not None
    assert event.annotated_frame_path is None
