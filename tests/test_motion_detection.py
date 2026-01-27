"""Tests for motion detection functionality."""

import uuid
import asyncio
import pytest
import numpy as np
import cv2

from src.capture.motion_detector import MotionDetector
from src.capture.camera import CameraConfig


@pytest.mark.asyncio
async def test_motion_detector_initialization():
    """Test MotionDetector initialization with default threshold."""
    detector = MotionDetector(threshold=10.0)
    assert detector.threshold == 10.0


@pytest.mark.asyncio
async def test_motion_detector_invalid_threshold():
    """Test MotionDetector rejects invalid threshold."""
    detector = MotionDetector(threshold=10.0)

    with pytest.raises(ValueError, match="must be between 0 and 100"):
        detector.update_threshold(150.0)

    with pytest.raises(ValueError, match="must be between 0 and 100"):
        detector.update_threshold(-5.0)


@pytest.mark.asyncio
async def test_motion_detector_reset():
    """Test MotionDetector reset functionality."""
    detector = MotionDetector(threshold=10.0)

    # Create a dummy frame
    frame = np.zeros((240, 320, 3), dtype=np.uint8)
    await asyncio.get_event_loop().run_in_executor(
        None, lambda: detector.detect_motion(frame)
    )

    # Reset should clear previous frame
    detector.reset()
    # Detector should treat next frame as first frame


@pytest.mark.asyncio
async def test_static_scene_no_motion():
    """Test that static scene returns low motion score."""
    detector = MotionDetector(threshold=10.0)

    # Create static frames (all black)
    frame1 = np.zeros((240, 320, 3), dtype=np.uint8)
    frame2 = np.zeros((240, 320, 3), dtype=np.uint8)

    loop = asyncio.get_event_loop()
    score1, motion1 = await loop.run_in_executor(None, detector.detect_motion, frame1)
    score2, motion2 = await loop.run_in_executor(None, detector.detect_motion, frame2)

    # First frame should always be sent
    assert motion1 is True

    # Second static frame should be filtered
    assert motion2 is False
    assert score2 < 10.0


@pytest.mark.asyncio
async def test_scene_with_movement():
    """Test that scene with movement returns high motion score."""
    detector = MotionDetector(threshold=10.0)

    # Create frames with movement (different pixel values)
    frame1 = np.zeros((240, 320, 3), dtype=np.uint8)
    frame2 = np.ones((240, 320, 3), dtype=np.uint8) * 255  # Bright change

    loop = asyncio.get_event_loop()
    score1, motion1 = await loop.run_in_executor(None, detector.detect_motion, frame1)
    score2, motion2 = await loop.run_in_executor(None, detector.detect_motion, frame2)

    # First frame should be sent
    assert motion1 is True

    # Second frame with movement should be sent
    assert motion2 is True
    assert score2 > 10.0


@pytest.mark.asyncio
async def test_threshold_sensitivity():
    """Test that different thresholds affect filtering."""
    # Create frames with small movement
    frame1 = np.zeros((240, 320, 3), dtype=np.uint8)
    frame2 = np.ones((240, 320, 3), dtype=np.uint8) * 50  # Small change

    loop = asyncio.get_event_loop()

    # Low threshold - should detect motion
    detector_low = MotionDetector(threshold=1.0)
    await loop.run_in_executor(None, detector_low.detect_motion, frame1)
    score_low, motion_low = await loop.run_in_executor(
        None, detector_low.detect_motion, frame2
    )
    assert motion_low is True

    # High threshold - should filter (create very small change)
    detector_high = MotionDetector(threshold=50.0)
    await loop.run_in_executor(None, detector_high.detect_motion, frame1)
    frame3 = np.ones((240, 320, 3), dtype=np.uint8) * 5  # Very small change
    score_high, motion_high = await loop.run_in_executor(
        None, detector_high.detect_motion, frame3
    )
    assert motion_high is False


@pytest.mark.asyncio
async def test_motion_detector_update_threshold():
    """Test updating threshold dynamically."""
    detector = MotionDetector(threshold=10.0)
    assert detector.threshold == 10.0

    detector.update_threshold(5.0)
    assert detector.threshold == 5.0


@pytest.mark.asyncio
async def test_camera_config_motion_detection_defaults():
    """Test CameraConfig uses settings defaults for motion detection."""
    from src.config import settings

    config = CameraConfig(
        id=uuid.uuid4(),
        name="Test Camera",
        url="rtsp://test.com/stream",
    )

    assert config.motion_detection_enabled == settings.motion_detection_enabled
    assert config.motion_threshold == settings.motion_threshold


@pytest.mark.asyncio
async def test_camera_config_explicit_motion_settings():
    """Test CameraConfig allows explicit motion detection settings."""
    config = CameraConfig(
        id=uuid.uuid4(),
        name="Test Camera",
        url="rtsp://test.com/stream",
        motion_detection_enabled=False,
        motion_threshold=5.0,
    )

    assert config.motion_detection_enabled is False
    assert config.motion_threshold == 5.0


@pytest.mark.asyncio
async def test_camera_state_motion_statistics():
    """Test CameraState tracks motion statistics correctly."""
    from src.capture.camera import CameraConfig, CameraState

    config = CameraConfig(
        id=uuid.uuid4(),
        name="Test Camera",
        url="rtsp://test.com/stream",
    )
    state = CameraState(config=config)

    # Initial stats
    assert state.frames_captured == 0
    assert state.frames_sent == 0
    assert state.frames_filtered == 0
    assert state.detection_rate == 0.0

    # Record frames
    state.record_frame(100.0)
    state.record_sent_frame(15.5)
    state.record_frame(101.0)
    state.record_sent_frame(20.0)
    state.record_frame(102.0)
    state.record_filtered_frame()

    assert state.frames_captured == 3
    assert state.frames_sent == 2
    assert state.frames_filtered == 1
    assert round(state.detection_rate, 2) == 66.67  # 2/3 * 100
    assert round(state.avg_motion_score, 2) == 17.75  # (15.5 + 20) / 2


@pytest.mark.asyncio
async def test_camera_state_reset_clears_motion_stats():
    """Test CameraState.reset_stats clears motion statistics."""
    from src.capture.camera import CameraConfig, CameraState

    config = CameraConfig(
        id=uuid.uuid4(),
        name="Test Camera",
        url="rtsp://test.com/stream",
    )
    state = CameraState(config=config)

    # Add some stats
    state.record_frame(100.0)
    state.record_sent_frame(10.0)
    state.record_filtered_frame()
    state.record_error("Test error")

    # Reset
    state.reset_stats()

    assert state.frames_captured == 0
    assert state.frames_sent == 0
    assert state.frames_filtered == 0
    assert state.avg_motion_score == 0.0
    assert state.motion_score_sum == 0.0
    assert state.errors_count == 0
    assert state.last_error is None


@pytest.mark.asyncio
async def test_improved_sensitivity_vehicle_lateral_movement():
    """Test improved algorithm detects lateral vehicle movement."""
    detector = MotionDetector(threshold=10.0)

    # Create frames simulating vehicle passing (lateral movement)
    # Frame 1: static street scene
    frame1 = np.zeros((480, 640, 3), dtype=np.uint8)
    # Add static background (buildings, sky)
    frame1[200:480, :, :] = 50  # Road
    frame1[0:200, :, :] = 100  # Sky/buildings

    # Frame 2: vehicle appears on left side
    frame2 = frame1.copy()
    # Draw a "vehicle" (rectangular block with moderate contrast)
    frame2[250:350, 50:150, :] = 120  # Vehicle body

    loop = asyncio.get_event_loop()
    score1, motion1 = await loop.run_in_executor(None, detector.detect_motion, frame1)
    score2, motion2 = await loop.run_in_executor(None, detector.detect_motion, frame2)

    # First frame should be sent
    assert motion1 is True

    # Vehicle movement should produce score >= 10% with improved sensitivity
    assert motion2 is True, (
        f"Vehicle lateral movement not detected, score={score2:.2f}%"
    )
    assert score2 >= 10.0, f"Score too low for vehicle: {score2:.2f}%, expected >= 10%"


@pytest.mark.asyncio
async def test_improved_sensitivity_person_walking():
    """Test improved algorithm detects person walking."""
    detector = MotionDetector(threshold=10.0)

    # Create frames simulating person walking
    frame1 = np.ones((480, 640, 3), dtype=np.uint8) * 80  # Indoor scene

    # Person appears (smaller than vehicle)
    frame2 = frame1.copy()
    frame2[200:400, 300:350, :] = 150  # Person silhouette

    loop = asyncio.get_event_loop()
    score1, motion1 = await loop.run_in_executor(None, detector.detect_motion, frame1)
    score2, motion2 = await loop.run_in_executor(None, detector.detect_motion, frame2)

    # First frame always sent
    assert motion1 is True

    # Person walking should be detected with improved sensitivity
    assert motion2 is True, f"Person walking not detected, score={score2:.2f}%"
    assert score2 >= 10.0, f"Score too low for person: {score2:.2f}%, expected >= 10%"


@pytest.mark.asyncio
async def test_improved_sensitivity_static_outdoor_scene():
    """Test improved algorithm still filters static outdoor scenes."""
    detector = MotionDetector(threshold=10.0)

    # Create outdoor static scene with varied content
    frame1 = np.random.randint(40, 120, (480, 640, 3), dtype=np.uint8)  # Textured scene
    frame2 = frame1.copy()  # Exact same frame

    loop = asyncio.get_event_loop()
    score1, motion1 = await loop.run_in_executor(None, detector.detect_motion, frame1)
    score2, motion2 = await loop.run_in_executor(None, detector.detect_motion, frame2)

    # First frame sent
    assert motion1 is True

    # Static scene should still be filtered despite improved sensitivity
    assert motion2 is False, (
        f"Static scene incorrectly detected as motion, score={score2:.2f}%"
    )
    assert score2 < 5.0, f"Static scene score too high: {score2:.2f}%, expected < 5%"


@pytest.mark.asyncio
async def test_improved_sensitivity_score_ranges():
    """Test that improved algorithm produces expected score ranges."""
    detector = MotionDetector(threshold=10.0)

    loop = asyncio.get_event_loop()

    # Baseline
    frame1 = np.ones((480, 640, 3), dtype=np.uint8) * 100
    score1, _ = await loop.run_in_executor(None, detector.detect_motion, frame1)

    # Small change (subtle motion) - should now detect better
    frame2 = frame1.copy()
    frame2[200:300, 200:400, :] = 115  # 15-point change over 10% of frame
    score2, motion2 = await loop.run_in_executor(None, detector.detect_motion, frame2)

    # Large change (significant motion)
    frame3 = frame1.copy()
    frame3[100:400, 100:500, :] = 200  # Large bright area
    score3, motion3 = await loop.run_in_executor(None, detector.detect_motion, frame3)

    # With improved parameters, subtle motion should be detectable
    assert score2 >= 10.0, f"Subtle motion score {score2:.2f}% should be >= 10%"
    assert motion2 is True

    # Large motion should produce higher score
    assert score3 > score2, (
        f"Large motion ({score3:.2f}%) should exceed subtle motion ({score2:.2f}%)"
    )
    assert motion3 is True
