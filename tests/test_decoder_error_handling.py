"""Tests for H.264 decoder error handling."""

import uuid
import pytest
import numpy as np

from src.capture.frame_grabber import FrameGrabber
from src.capture.camera import CameraConfig, CameraState


@pytest.mark.asyncio
async def test_validate_frame_valid():
    """Test that valid frames pass validation."""
    from src.config import settings

    config = CameraConfig(
        id=uuid.uuid4(),
        name="Test Camera",
        url="rtsp://test.com/stream",
    )

    grabber = FrameGrabber(camera_config=config)

    # Create valid frame
    frame = np.random.randint(0, 255, (240, 320, 3), dtype=np.uint8)

    result = grabber._validate_frame(frame)

    assert result is True


@pytest.mark.asyncio
async def test_validate_frame_none():
    """Test that None frames fail validation."""
    from src.config import settings

    config = CameraConfig(
        id=uuid.uuid4(),
        name="Test Camera",
        url="rtsp://test.com/stream",
    )

    grabber = FrameGrabber(camera_config=config)

    result = grabber._validate_frame(None)

    assert result is False


@pytest.mark.asyncio
async def test_validate_frame_empty():
    """Test that empty frames fail validation."""
    from src.config import settings

    config = CameraConfig(
        id=uuid.uuid4(),
        name="Test Camera",
        url="rtsp://test.com/stream",
    )

    grabber = FrameGrabber(camera_config=config)

    # Create empty frame
    frame = np.array([])

    result = grabber._validate_frame(frame)

    assert result is False


@pytest.mark.asyncio
async def test_validate_frame_uniform_color():
    """Test that uniform color frames fail validation."""
    from src.config import settings

    config = CameraConfig(
        id=uuid.uuid4(),
        name="Test Camera",
        url="rtsp://test.com/stream",
    )

    grabber = FrameGrabber(camera_config=config)

    # Create uniform color frame (all black)
    frame = np.zeros((240, 320, 3), dtype=np.uint8)

    result = grabber._validate_frame(frame)

    assert result is False


@pytest.mark.asyncio
async def test_validate_frame_low_resolution():
    """Test that low resolution frames fail validation."""
    from src.config import settings

    config = CameraConfig(
        id=uuid.uuid4(),
        name="Test Camera",
        url="rtsp://test.com/stream",
    )

    grabber = FrameGrabber(camera_config=config)

    # Create low resolution frame (below 160x120 minimum)
    frame = np.random.randint(0, 255, (100, 80, 3), dtype=np.uint8)

    result = grabber._validate_frame(frame)

    assert result is False


@pytest.mark.asyncio
async def test_validate_frame_minimal_valid_resolution():
    """Test that minimum valid resolution frames pass validation."""
    from src.config import settings

    config = CameraConfig(
        id=uuid.uuid4(),
        name="Test Camera",
        url="rtsp://test.com/stream",
    )

    grabber = FrameGrabber(camera_config=config)

    # Create minimum valid resolution frame (160x120)
    frame = np.random.randint(0, 255, (120, 160, 3), dtype=np.uint8)

    result = grabber._validate_frame(frame)

    assert result is True


@pytest.mark.asyncio
async def test_camera_state_decoder_error_tracking():
    """Test CameraState tracks decoder errors correctly."""
    from src.config import settings

    config = CameraConfig(
        id=uuid.uuid4(),
        name="Test Camera",
        url="rtsp://test.com/stream",
    )
    state = CameraState(config=config)

    # Initial state
    assert state.decoder_error_count == 0
    assert state.decoder_error_rate == 0.0
    assert state.last_decoder_error is None

    # Record some frames
    state.record_frame(100.0)
    state.record_frame(101.0)
    state.record_frame(102.0)

    # Record decoder errors
    state.record_decoder_error("missing picture in access unit")
    state.record_decoder_error("no frame")

    # Verify tracking
    assert state.decoder_error_count == 2
    assert round(state.decoder_error_rate, 2) == 66.67  # 2/3 * 100
    assert state.last_decoder_error == "no frame"


@pytest.mark.asyncio
async def test_camera_state_decoder_error_rate_no_frames():
    """Test decoder error rate when no frames captured."""
    from src.config import settings

    config = CameraConfig(
        id=uuid.uuid4(),
        name="Test Camera",
        url="rtsp://test.com/stream",
    )
    state = CameraState(config=config)

    # Record decoder error with no frames
    state.record_decoder_error("test error")

    # Verify rate is 0.0 (not division by zero)
    assert state.decoder_error_count == 1
    assert state.decoder_error_rate == 0.0
