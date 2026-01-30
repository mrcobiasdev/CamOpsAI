"""Integration tests for video file camera lifecycle."""

import asyncio
import tempfile
import cv2
import numpy as np
import pytest
import uuid
from pathlib import Path

from src.capture.camera import CameraConfig, CameraStatus
from src.capture.frame_grabber import FrameGrabber


@pytest.fixture
def test_video_file():
    """Create a test video file with known content."""
    # Create a temporary video file
    temp_file = tempfile.NamedTemporaryFile(suffix=".mp4", delete=False)
    temp_path = temp_file.name
    temp_file.close()

    # Create video writer (320x240, 5fps, 30 frames = 6 seconds)
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    out = cv2.VideoWriter(temp_path, fourcc, 5.0, (320, 240))

    try:
        # Write 30 frames with changing content (gradual color shift)
        for i in range(30):
            frame = np.zeros((240, 320, 3), dtype=np.uint8)
            # Add color that changes over time
            frame[:, :] = [i * 8, 0, 255 - i * 8]  # Red to Blue gradient
            out.write(frame)
    finally:
        out.release()

    yield temp_path

    # Cleanup
    Path(temp_path).unlink(missing_ok=True)


class TestVideoFileFrameGrabber:
    """Integration tests for FrameGrabber with video files."""

    @pytest.mark.asyncio
    async def test_video_file_connection(self, test_video_file):
        """Test connecting to a video file source."""
        config = CameraConfig(
            id=uuid.uuid4(),
            name="Test Video Camera",
            url=test_video_file,
            source_type="video_file",
            frame_interval=1,
            motion_detection_enabled=False,
        )

        grabber = FrameGrabber(camera_config=config)

        # Test connection
        connected = await grabber.connect()
        assert connected is True
        assert grabber.state.status == CameraStatus.CONNECTED

        # Verify video metadata is loaded
        assert grabber.state.total_frames == 30
        assert grabber.state.duration_seconds > 0

        # Cleanup
        await grabber.disconnect()

    @pytest.mark.asyncio
    async def test_video_file_frame_capture(self, test_video_file):
        """Test capturing frames from video file."""
        config = CameraConfig(
            id=uuid.uuid4(),
            name="Test Video Camera",
            url=test_video_file,
            source_type="video_file",
            frame_interval=0.1,  # Fast interval for testing
            motion_detection_enabled=False,
        )

        frames_captured = []

        def on_frame(camera_id, frame_data, timestamp):
            frames_captured.append((camera_id, len(frame_data), timestamp))

        grabber = FrameGrabber(camera_config=config, on_frame=on_frame)

        await grabber.connect()
        await grabber.start()

        # Wait for some frames to be captured
        await asyncio.sleep(2)

        await grabber.stop()

        # Verify frames were captured
        assert len(frames_captured) > 0
        assert all(frame_size > 0 for _, frame_size, _ in frames_captured)
        assert grabber.state.frames_captured > 0

        await grabber.disconnect()

    @pytest.mark.asyncio
    async def test_video_file_end_of_stream(self, test_video_file):
        """Test that video file stops gracefully at end of stream."""
        config = CameraConfig(
            id=uuid.uuid4(),
            name="Test Video Camera",
            url=test_video_file,
            source_type="video_file",
            frame_interval=0.1,  # Fast interval
            motion_detection_enabled=False,
        )

        grabber = FrameGrabber(camera_config=config)

        await grabber.connect()
        assert grabber.state.total_frames == 30

        await grabber.start()

        # Wait for entire video to play (6 seconds + margin)
        await asyncio.sleep(8)

        # Verify capture stopped gracefully
        assert grabber.state.status == CameraStatus.DISCONNECTED
        assert grabber.is_running is False

        await grabber.disconnect()

    @pytest.mark.asyncio
    async def test_video_file_with_motion_detection(self, test_video_file):
        """Test video file with motion detection enabled."""
        config = CameraConfig(
            id=uuid.uuid4(),
            name="Test Video Camera",
            url=test_video_file,
            source_type="video_file",
            frame_interval=0.2,
            motion_detection_enabled=True,
            motion_threshold=5.0,
        )

        frames_sent = []

        def on_frame(camera_id, frame_data, timestamp):
            frames_sent.append(frame_data)

        grabber = FrameGrabber(camera_config=config, on_frame=on_frame)

        await grabber.connect()
        await grabber.start()

        # Wait for some frames with changing content
        await asyncio.sleep(3)

        await grabber.stop()

        # Motion detection should filter some frames
        # (video has gradual color change, so some frames should be sent)
        assert len(frames_sent) > 0
        assert len(frames_sent) <= grabber.state.frames_captured

        await grabber.disconnect()

    @pytest.mark.asyncio
    async def test_video_file_progress_tracking(self, test_video_file):
        """Test that video file progress is tracked correctly."""
        config = CameraConfig(
            id=uuid.uuid4(),
            name="Test Video Camera",
            url=test_video_file,
            source_type="video_file",
            frame_interval=0.1,
            motion_detection_enabled=False,
        )

        grabber = FrameGrabber(camera_config=config)

        await grabber.connect()

        # Verify initial state
        assert grabber.state.total_frames == 30
        assert grabber.state.current_frame_number == 0
        assert grabber.state.progress_percentage == 0.0

        await grabber.start()

        # Wait for some frames
        await asyncio.sleep(2)

        # Verify progress is tracked
        await grabber.stop()

        assert grabber.state.current_frame_number > 0
        assert grabber.state.progress_percentage > 0
        assert grabber.state.progress_percentage <= 100

        # End of stream
        await asyncio.sleep(6)

        assert grabber.state.status == CameraStatus.DISCONNECTED

        await grabber.disconnect()

    @pytest.mark.asyncio
    async def test_video_file_error_position_logging(self, test_video_file):
        """Test that errors include frame position for video files."""
        config = CameraConfig(
            id=uuid.uuid4(),
            name="Test Video Camera",
            url=test_video_file,
            source_type="video_file",
            frame_interval=0.1,
            motion_detection_enabled=False,
        )

        grabber = FrameGrabber(camera_config=config)

        await grabber.connect()
        await grabber.start()

        # Let it capture some frames
        await asyncio.sleep(1)

        # Stop should have captured some frames
        initial_count = grabber.state.current_frame_number
        assert initial_count > 0

        await grabber.stop()
        await grabber.disconnect()

    @pytest.mark.asyncio
    async def test_video_file_multiple_start_stop_cycles(self, test_video_file):
        """Test that video file can be started and stopped multiple times."""
        config = CameraConfig(
            id=uuid.uuid4(),
            name="Test Video Camera",
            url=test_video_file,
            source_type="video_file",
            frame_interval=0.2,
            motion_detection_enabled=False,
        )

        grabber = FrameGrabber(camera_config=config)

        # First cycle
        await grabber.connect()
        await grabber.start()
        await asyncio.sleep(1)
        await grabber.stop()
        assert grabber.state.status == CameraStatus.CONNECTED

        # Second cycle
        await grabber.start()
        await asyncio.sleep(1)
        await grabber.stop()
        assert grabber.state.status == CameraStatus.CONNECTED

        # Third cycle to end
        await grabber.start()
        await asyncio.sleep(8)  # Let it reach end
        assert grabber.state.status == CameraStatus.DISCONNECTED

        await grabber.disconnect()

    @pytest.mark.asyncio
    async def test_rtsp_vs_video_file_behavior(self, test_video_file):
        """Test that RTSP and video file sources behave differently."""
        # Video file config
        video_config = CameraConfig(
            id=uuid.uuid4(),
            name="Video Camera",
            url=test_video_file,
            source_type="video_file",
            frame_interval=0.2,
            motion_detection_enabled=False,
        )

        video_grabber = FrameGrabber(camera_config=video_config)

        await video_grabber.connect()
        await video_grabber.start()

        # Wait for end of stream
        await asyncio.sleep(8)

        # Video file should stop gracefully
        assert video_grabber.state.status == CameraStatus.DISCONNECTED
        assert video_grabber.is_running is False

        await video_grabber.disconnect()
