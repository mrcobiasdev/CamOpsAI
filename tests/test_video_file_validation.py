"""Tests for video file validation and camera configuration."""

import os
import tempfile
import pytest
from src.api.routes.cameras import detect_source_type, validate_video_file


class TestDetectSourceType:
    """Tests for detect_source_type function."""

    def test_detect_source_type_rtsp(self):
        """Test detection of RTSP source type."""
        assert detect_source_type("rtsp://192.168.1.1:554/stream") == "rtsp"
        assert detect_source_type("rtmp://192.168.1.1:1935/stream") == "rtsp"

    def test_detect_source_type_rtmp(self):
        """Test detection of RTMP source type."""
        assert detect_source_type("rtmp://example.com/live/stream") == "rtsp"

    def test_detect_source_type_existing_video_file(self, tmp_path):
        """Test detection of existing video file source type."""
        # Create a temporary video file
        video_file = tmp_path / "test.mp4"
        video_file.write_bytes(b"fake video content")

        assert detect_source_type(str(video_file)) == "video_file"

    def test_detect_source_type_non_existing_file(self):
        """Test detection defaults to rtsp for non-existing file."""
        assert detect_source_type("/non/existent/path.mp4") == "rtsp"

    def test_detect_source_type_environment_variable(self, tmp_path, monkeypatch):
        """Test detection with environment variable in path."""
        video_file = tmp_path / "test.mp4"
        video_file.write_bytes(b"fake video content")

        monkeypatch.setenv("TEST_VIDEO_DIR", str(tmp_path))
        assert detect_source_type("$TEST_VIDEO_DIR/test.mp4") == "video_file"


class TestValidateVideoFile:
    """Tests for validate_video_file function."""

    def test_validate_video_file_rtsp_source(self):
        """Test validation returns True for RTSP sources."""
        is_valid, error_msg = validate_video_file(
            "rtsp://192.168.1.1:554/stream", "rtsp"
        )
        assert is_valid is True
        assert error_msg == ""

    def test_validate_video_file_none_source_type(self):
        """Test validation returns True when source_type is None."""
        is_valid, error_msg = validate_video_file("/any/path.mp4", None)
        assert is_valid is True
        assert error_msg == ""

    def test_validate_video_file_non_existing_file(self, tmp_path):
        """Test validation fails for non-existing video file."""
        non_existent = str(tmp_path / "nonexistent.mp4")
        is_valid, error_msg = validate_video_file(non_existent, "video_file")

        assert is_valid is False
        assert "Video file not found" in error_msg
        assert non_existent in error_msg

    def test_validate_video_file_supported_formats(self, tmp_path):
        """Test validation accepts all supported video formats."""
        supported_extensions = [".mp4", ".avi", ".mov", ".mkv", ".webm", ".flv", ".m4v"]

        for ext in supported_extensions:
            video_file = tmp_path / f"test{ext}"
            video_file.write_bytes(b"fake video content")

            is_valid, error_msg = validate_video_file(str(video_file), "video_file")
            assert is_valid is True, f"Failed for extension {ext}"
            assert error_msg == ""

    def test_validate_video_file_unsupported_format(self, tmp_path):
        """Test validation rejects unsupported video format."""
        video_file = tmp_path / "test.txt"
        video_file.write_bytes(b"not a video")

        is_valid, error_msg = validate_video_file(str(video_file), "video_file")

        assert is_valid is False
        assert "Unsupported video format" in error_msg
        assert ".txt" in error_msg
        assert ".mp4" in error_msg  # Should list supported formats

    def test_validate_video_file_case_insensitive_extension(self, tmp_path):
        """Test validation is case insensitive for file extension."""
        video_file = tmp_path / "test.MP4"
        video_file.write_bytes(b"fake video content")

        is_valid, error_msg = validate_video_file(str(video_file), "video_file")
        assert is_valid is True
        assert error_msg == ""

    def test_validate_video_file_expands_environment_variables(
        self, tmp_path, monkeypatch
    ):
        """Test validation expands environment variables in path."""
        video_file = tmp_path / "test.mp4"
        video_file.write_bytes(b"fake video content")

        monkeypatch.setenv("MY_VIDEO_PATH", str(tmp_path))
        path_with_env = "$MY_VIDEO_PATH/test.mp4"

        is_valid, error_msg = validate_video_file(path_with_env, "video_file")
        assert is_valid is True
        assert error_msg == ""

    def test_validate_video_file_relative_to_absolute(self, tmp_path):
        """Test validation converts relative paths to absolute."""
        # Create a file in current directory
        with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as f:
            f.write(b"fake video content")
            temp_path = f.name

        try:
            # Get relative path
            cwd = os.getcwd()
            rel_path = os.path.relpath(temp_path, cwd)

            # Validate with relative path
            is_valid, error_msg = validate_video_file(rel_path, "video_file")
            assert is_valid is True
            assert error_msg == ""
        finally:
            os.unlink(temp_path)

    def test_validate_video_file_without_extension(self, tmp_path):
        """Test validation rejects file without extension."""
        video_file = tmp_path / "noextension"
        video_file.write_bytes(b"fake video content")

        is_valid, error_msg = validate_video_file(str(video_file), "video_file")

        assert is_valid is False
        assert "Unsupported video format" in error_msg
