"""Performance and edge case tests for motion detection."""

import uuid
import asyncio
import pytest
import numpy as np
import cv2
import time

from src.capture.motion_detector import MotionDetector
from src.capture.frame_grabber import FrameGrabber
from src.capture.camera import CameraConfig


@pytest.mark.asyncio
async def test_motion_detection_performance_under_50ms():
    """Test that motion detection completes in under 50ms."""
    detector = MotionDetector(threshold=10.0)

    # Create a realistic frame
    frame = np.random.randint(0, 255, (1080, 1920, 3), dtype=np.uint8)

    # Encode to JPEG (simulates real workflow)
    _, buffer = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 85])
    frame_bytes = buffer.tobytes()

    loop = asyncio.get_event_loop()

    # Warm up
    await loop.run_in_executor(None, detector.detect_motion, frame)

    # Measure 10 iterations
    times = []
    for _ in range(10):
        start = time.perf_counter()
        score, motion = await loop.run_in_executor(None, detector.detect_motion, frame)
        end = time.perf_counter()
        times.append((end - start) * 1000)  # Convert to ms

    avg_time = sum(times) / len(times)
    max_time = max(times)

    assert avg_time < 50, f"Average time {avg_time:.2f}ms exceeds 50ms"
    assert max_time < 100, f"Max time {max_time:.2f}ms too high"


@pytest.mark.asyncio
async def test_motion_detector_low_light_noise():
    """Test motion detection with low light noise."""
    detector = MotionDetector(threshold=15.0)  # Higher threshold for noise

    # Create frames with noise (simulating low light)
    np.random.seed(42)
    frame1 = np.random.randint(30, 60, (240, 320, 3), dtype=np.uint8)
    frame2 = np.random.randint(30, 60, (240, 320, 3), dtype=np.uint8)

    loop = asyncio.get_event_loop()

    score1, motion1 = await loop.run_in_executor(None, detector.detect_motion, frame1)
    score2, motion2 = await loop.run_in_executor(None, detector.detect_motion, frame2)

    # First frame always sent
    assert motion1 is True

    # Second noisy frame should be filtered (low motion due to high threshold)
    assert motion2 is False
    assert score2 < 15.0


@pytest.mark.asyncio
async def test_motion_detector_sudden_lighting_change():
    """Test motion detection with sudden lighting change."""
    detector = MotionDetector(threshold=10.0)

    # Dark frame then bright frame
    frame1 = np.zeros((240, 320, 3), dtype=np.uint8)
    frame2 = np.ones((240, 320, 3), dtype=np.uint8) * 255

    loop = asyncio.get_event_loop()

    score1, motion1 = await loop.run_in_executor(None, detector.detect_motion, frame1)
    score2, motion2 = await loop.run_in_executor(None, detector.detect_motion, frame2)

    # First frame always sent
    assert motion1 is True

    # Sudden lighting should trigger motion detection
    assert motion2 is True
    assert score2 > 50.0


@pytest.mark.asyncio
async def test_motion_detector_camera_reconnection_resets_state():
    """Test that camera reconnection resets motion detector state."""
    config = CameraConfig(
        id=uuid.uuid4(),
        name="Test Camera",
        url="rtsp://test.com/stream",
        motion_detection_enabled=True,
        motion_threshold=10.0,
    )

    grabber = FrameGrabber(camera_config=config)

    # Create frames
    frame1 = np.zeros((240, 320, 3), dtype=np.uint8)
    frame2 = np.zeros((240, 320, 3), dtype=np.uint8)

    _, buffer1 = cv2.imencode(".jpg", frame1, [cv2.IMWRITE_JPEG_QUALITY, 85])
    _, buffer2 = cv2.imencode(".jpg", frame2, [cv2.IMWRITE_JPEG_QUALITY, 85])

    frame1_bytes = buffer1.tobytes()
    frame2_bytes = buffer2.tobytes()

    loop = asyncio.get_event_loop()

    # First frame should pass
    should_send1 = await grabber._check_motion(frame1_bytes)
    assert should_send1 is True

    # Second frame should be filtered
    should_send2 = await grabber._check_motion(frame2_bytes)
    assert should_send2 is False

    # Simulate reconnection (reset detector)
    grabber._motion_detector.reset()

    # After reset, first frame should pass again
    frame3 = np.zeros((240, 320, 3), dtype=np.uint8)
    _, buffer3 = cv2.imencode(".jpg", frame3, [cv2.IMWRITE_JPEG_QUALITY, 85])
    frame3_bytes = buffer3.tobytes()

    should_send3 = await grabber._check_motion(frame3_bytes)
    assert should_send3 is True


@pytest.mark.asyncio
async def test_motion_detector_fail_safety():
    """Test that motion detection failures send frame to LLM (fail-safe)."""
    config = CameraConfig(
        id=uuid.uuid4(),
        name="Test Camera",
        url="rtsp://test.com/stream",
        motion_detection_enabled=True,
        motion_threshold=10.0,
    )

    grabber = FrameGrabber(camera_config=config)

    # Invalid JPEG data (should cause error in motion detection)
    invalid_frame = b"\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x00\x00\x00\x00\x00"

    # Should return True (send to LLM) on error
    should_send = await grabber._check_motion(invalid_frame)
    assert should_send is True  # Fail-safe: send frame if detection fails


@pytest.mark.asyncio
async def test_motion_detector_threshold_updates_dynamically():
    """Test that threshold can be updated on running camera."""
    config = CameraConfig(
        id=uuid.uuid4(),
        name="Test Camera",
        url="rtsp://test.com/stream",
        motion_detection_enabled=True,
        motion_threshold=50.0,  # High threshold
    )

    grabber = FrameGrabber(camera_config=config)

    # Create frames
    frame1 = np.zeros((240, 320, 3), dtype=np.uint8)

    _, buffer1 = cv2.imencode(".jpg", frame1, [cv2.IMWRITE_JPEG_QUALITY, 85])

    frame1_bytes = buffer1.tobytes()

    loop = asyncio.get_event_loop()

    # First frame always sent
    should_send1 = await grabber._check_motion(frame1_bytes)
    assert should_send1 is True

    # Same frame (static) should be filtered
    should_send2 = await grabber._check_motion(frame1_bytes)
    assert should_send2 is False

    # Update threshold to low value
    grabber._motion_detector.update_threshold(1.0)
    assert grabber._motion_detector.threshold == 1.0

    # Reset and test - first frame always sent
    grabber._motion_detector.reset()
    should_send3 = await grabber._check_motion(frame1_bytes)
    assert should_send3 is True

    # Second static frame should be filtered
    should_send4 = await grabber._check_motion(frame1_bytes)
    assert should_send4 is False


@pytest.mark.asyncio
async def test_api_reduction_simulation():
    """Simulate API call reduction with static vs active scenes."""
    config = CameraConfig(
        id=uuid.uuid4(),
        name="Test Camera",
        url="rtsp://test.com/stream",
        motion_detection_enabled=True,
        motion_threshold=10.0,
    )

    grabber = FrameGrabber(camera_config=config)

    # Simulate 100 frames of static scene
    np.random.seed(42)
    static_frames = 0
    for i in range(100):
        # Very static - same value every time
        frame = np.full((240, 320, 3), 102, dtype=np.uint8)
        _, buffer = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 85])
        frame_bytes = buffer.tobytes()

        should_send = await grabber._check_motion(frame_bytes)
        if should_send:
            static_frames += 1

    # With 100 frames, expect ~1 sent (first frame only)
    reduction_rate = (100 - static_frames) / 100 * 100
    assert reduction_rate > 95, f"Expected >95% reduction, got {reduction_rate:.1f}%"

    # Reset for active scene simulation
    grabber._motion_detector.reset()

    # Simulate 100 frames with periodic movement
    active_frames = 0
    for i in range(100):
        if i % 10 == 0:  # Every 10th frame has movement
            frame = np.ones((240, 320, 3), dtype=np.uint8) * 255
        else:
            frame = np.zeros((240, 320, 3), dtype=np.uint8)

        _, buffer = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 85])
        frame_bytes = buffer.tobytes()

        should_send = await grabber._check_motion(frame_bytes)
        if should_send:
            active_frames += 1

    # With periodic movements, expect more frames sent
    # Background subtraction + pixel difference may trigger on movement
    assert active_frames >= 10, f"Expected at least 10 frames sent, got {active_frames}"

    active_reduction_rate = (100 - active_frames) / 100 * 100
    assert active_reduction_rate > 75, (
        f"Expected >75% reduction even with movement, got {active_reduction_rate:.1f}%"
    )
