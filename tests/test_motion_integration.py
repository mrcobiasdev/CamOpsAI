"""Integration tests for MotionDetector with FrameGrabber."""

import uuid
import asyncio
import pytest
import numpy as np
import cv2

from src.capture.frame_grabber import FrameGrabber
from src.capture.camera import CameraConfig


@pytest.mark.asyncio
async def test_framegrabber_uses_motion_detector():
    """Test that FrameGrabber initializes MotionDetector."""
    config = CameraConfig(
        id=uuid.uuid4(),
        name="Test Camera",
        url="rtsp://test.com/stream",
        motion_detection_enabled=True,
        motion_threshold=10.0,
    )

    grabber = FrameGrabber(camera_config=config)
    assert grabber._motion_detector is not None
    assert grabber._motion_detector.threshold == 10.0


@pytest.mark.asyncio
async def test_framegrabber_no_motion_when_disabled():
    """Test that FrameGrabber skips motion detection when disabled."""
    config = CameraConfig(
        id=uuid.uuid4(),
        name="Test Camera",
        url="rtsp://test.com/stream",
        motion_detection_enabled=False,
    )

    grabber = FrameGrabber(camera_config=config)
    assert grabber._motion_detector is None


@pytest.mark.asyncio
async def test_framegrabber_tracks_motion_statistics():
    """Test that FrameGrabber tracks motion statistics."""
    config = CameraConfig(
        id=uuid.uuid4(),
        name="Test Camera",
        url="rtsp://test.com/stream",
        motion_detection_enabled=True,
        motion_threshold=5.0,
    )

    grabber = FrameGrabber(camera_config=config)

    # Simulate frame processing
    state = grabber.state
    assert state.frames_captured == 0
    assert state.frames_sent == 0
    assert state.frames_filtered == 0

    # Record some frames
    state.record_frame(100.0)
    state.record_sent_frame(15.5)
    state.record_frame(101.0)
    state.record_sent_frame(20.0)
    state.record_frame(102.0)
    state.record_filtered_frame()

    assert state.frames_captured == 3
    assert state.frames_sent == 2
    assert state.frames_filtered == 1
    assert round(state.detection_rate, 2) == 66.67


@pytest.mark.asyncio
async def test_motion_detector_with_framegrabber_integration():
    """Test MotionDetector integration with FrameGrabber."""
    config = CameraConfig(
        id=uuid.uuid4(),
        name="Test Camera",
        url="rtsp://test.com/stream",
        motion_detection_enabled=True,
        motion_threshold=10.0,
    )

    grabber = FrameGrabber(camera_config=config)

    # Create test frames
    frame1 = np.zeros((240, 320, 3), dtype=np.uint8)
    frame2 = np.zeros((240, 320, 3), dtype=np.uint8)
    frame3 = np.ones((240, 320, 3), dtype=np.uint8) * 255  # Motion

    # Encode to JPEG
    _, buffer1 = cv2.imencode(".jpg", frame1, [cv2.IMWRITE_JPEG_QUALITY, 85])
    _, buffer2 = cv2.imencode(".jpg", frame2, [cv2.IMWRITE_JPEG_QUALITY, 85])
    _, buffer3 = cv2.imencode(".jpg", frame3, [cv2.IMWRITE_JPEG_QUALITY, 85])

    frame1_bytes = buffer1.tobytes()
    frame2_bytes = buffer2.tobytes()
    frame3_bytes = buffer3.tobytes()

    # Test motion checking
    loop = asyncio.get_event_loop()

    # First frame should always pass
    should_send1 = await grabber._check_motion(frame1_bytes)
    assert should_send1 is True

    # Second static frame should be filtered
    should_send2 = await grabber._check_motion(frame2_bytes)
    assert should_send2 is False

    # Third frame with motion should pass
    should_send3 = await grabber._check_motion(frame3_bytes)
    assert should_send3 is True
